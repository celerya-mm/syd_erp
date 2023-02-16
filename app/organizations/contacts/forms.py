from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from config import db
from .models import Contact
from app.functions import not_empty, mount_full_name


def list_contacts():
	records = Contact.query.all()
	_list = [x.to_dict() for x in records]

	_contact = [d["full_name"] for d in _list]
	_email = [d["email"] for d in _list]

	db.session.close()
	return _contact, _email


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.all()
		_dict = [x.to_dict() for x in records]
		db.session.close()
		for d in _dict:
			_list.append(f"{str(d['id'])} - {d['organization']}")
	except Exception as err:
		db.session.close()
		print(err)
		pass

	return _list


list_roles = ['Amministratore Delegato', 'Referente Commerciale', 'Referente Tecnico', 'Referente Amministrativo',
			  'Referente Acquisti', 'Responsabile IT', 'Direttore Stabilimento', 'Direttore Amministrativo']


class FormContactCreate(FlaskForm):
	"""Form per creare un Contatto."""
	name = StringField('Nome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=25)])
	last_name = StringField('Cognome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=50)])

	role = SelectField('Ruolo', choices=list_roles)

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()], default="+39 ")

	partner_id = SelectField("Seleziona Partner", choices=list_partners())

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SIGNUP")

	def __repr__(self):
		return f'<CONTACT: {self.name} {self.last_name}>'

	def __str__(self):
		return f'<CONTACT: {self.name} {self.last_name}>'

	def validate_full_name(self):  # noqa
		"""Verifica presenza organization nella tabella del DB."""
		if f'{self.name.data} {self.last_name.data}' in list_contacts()[0]:
			raise ValidationError(f"Contatto già presente in tabella contacts: {self.name.data} {self.last_name.data}.")

	def validate_email(self, field):  # noqa
		"""Verifica email già assegnata a partner nella tabella del DB."""
		if field.data.strip() in list_contacts()[1]:
			raise ValidationError("Email già assegnata in tabella contacts.")


class FormContactUpdate(FlaskForm):
	"""Form per modificare un Contatto."""
	name = StringField('Nome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=25)])
	last_name = StringField('Cognome', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=50)])

	role = SelectField('Ruolo', choices=list_roles)

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()], default="+39 ")

	partner_id = SelectField("Seleziona Partner", choices=list_partners())

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SIGNUP")

	def __repr__(self):
		return f'<CONTACT: {self.name} {self.last_name}>'

	def __str__(self):
		return f'<CONTACT: {self.name} {self.last_name}>'

	def to_dict(self):
		"""Converte form in dict."""
		return {
			'name': self.name.data.strip(),
			'last_name': self.last_name.data.strip(),
			'full_name': mount_full_name(self.name.data, self.last_name.data),

			'role': self.role.data,

			'partner_id': self.partner_id.data.split(' - ')[0],

			'email': self.email.data.strip().replace(" ", ""),
			'phone': not_empty(self.phone.data.strip()),

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
