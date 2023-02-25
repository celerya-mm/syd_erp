from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.app import db, session
from .models import PartnerContact
from app.functions import not_empty, mount_full_name, list_roles


def list_partner_contacts():
	try:
		records = PartnerContact.query.all()
		if 'partner_id' in session.keys():
			_list = [x.to_dict() for x in records if x.partner_id != session['partner_id']]
		else:
			_list = [x.to_dict() for x in records]

		_contact = [d["full_name"] for d in _list]
		_email = [d["email"] for d in _list]

		db.session.close()
		return _contact, _email
	except Exception as err:
		print('ERROR_LIST_PARTNER_CONTACTS', err)
		db.session.close()
		return [], []


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")
	except Exception as err:
		print('ERROR_LIST_PARTNERS', err)
		pass

	db.session.close()
	return _list


def list_partner_sites():
	from app.organizations.partner_sites.models import PartnerSite

	_list = ["-"]
	try:
		records = PartnerSite.query.filter_by(partner_id=session['partner_id'])
		for r in records:
			_list.append(f"{r.id} - {r.site}")
	except Exception as err:
		print('ERROR_LIST_PARTNER_SITES', err)
		pass

	db.session.close()
	return _list


class FormPartnerContact(FlaskForm):
	"""Form per creare un Contatto."""
	name = StringField('Nome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=25)])
	last_name = StringField('Cognome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=50)])

	role = SelectField('Ruolo', choices=list_roles)

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Optional(), Length(min=7, max=25)], default="+39 ")

	partner_id = SelectField("Seleziona Partner")
	partner_site_id = SelectField("Seleziona Sito")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SIGNUP")

	def __repr__(self):
		return f'<PARTNER_CONTACT: {self.name} {self.last_name}>'

	def __str__(self):
		return f'<PARTNER_CONTACT: {self.name} {self.last_name}>'

	@classmethod
	def new(cls):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites()
		return form

	@classmethod
	def update(cls, obj):
		# Instantiate the form
		form = cls()
		form.name.data = obj.name
		form.last_name.data = obj.last_name

		form.role.data = obj.role

		form.email.data = obj.email
		form.phone.data = obj.phone if obj.phone else None

		# Update the choices
		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites()

		form.note.data = obj.note if obj.note else None
		return form

	def validate_full_name(self):  # noqa
		"""Verifica presenza contatto nella tabella del DB."""
		if f'{self.name.data} {self.last_name.data}' in list_partner_contacts()[0]:
			raise ValidationError(f"Contatto già presente in tabella contacts: {self.name.data} {self.last_name.data}.")

	def validate_email(self, field):  # noqa
		"""Verifica email già assegnata a partner nella tabella del DB."""
		if field.data.strip() in list_partner_contacts()[1]:
			raise ValidationError("Email già assegnata in tabella contacts.")

	def to_dict(self):
		"""Converte form in dict."""
		if self.partner_site_id.data and self.partner_site_id.data != '-':
			partner_site_id = self.partner_site_id.data.split(' - ')[0]
		else:
			partner_site_id = None

		return {
			'name': self.name.data.strip(),
			'last_name': self.last_name.data.strip(),
			'full_name': mount_full_name(self.name.data, self.last_name.data),

			'role': self.role.data,

			'partner_id': self.partner_id.data.split(' - ')[0],
			'partner_site_id': partner_site_id,

			'email': self.email.data.strip().replace(" ", ""),
			'phone': not_empty(self.phone.data.strip()),

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
