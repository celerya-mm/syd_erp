from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.app import db, session
from app.functions import mount_full_address, not_empty, status_true_false
from app.support_lists import site_type
from .models import PartnerSite


def list_partner_sites():
	try:
		records = PartnerSite.query.all()
		if 'partner_site_id' in session.keys():
			_list = [x.to_dict() for x in records if x.id != session['partner_site_id']]
		else:
			_list = [x.to_dict() for x in records]

		_list = [d["site"].lower() for d in _list]

		db.session.close()
		return _list
	except Exception as err:
		db.session.close()
		print('ERROR_LIST_PARTNER_SITES', err)
		return [], []


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.order_by(Partner.id.asc()).all()
		_dict = [x.to_dict() for x in records]
		for d in _dict:
			_list.append(f"{str(d['id'])} - {d['organization']}")
	except Exception as err:
		print('ERROR_LIST_PARTNERS', err)
		pass

	db.session.close()
	return _list


class FormPartnerSite(FlaskForm):
	"""Form per creare un Partner."""
	site = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	active = BooleanField('Stato', false_values=(False, 0))
	site_type = SelectField("Seleziona Tipo", validators=[DataRequired("Campo obbligatorio!")], choices=site_type)

	client = BooleanField('C', false_values=(False, 0))
	supplier = BooleanField('F', false_values=(False, 0))
	partner = BooleanField('P', false_values=(False, 0))

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	pec = EmailField('pec', validators=[Email(), Optional(), Length(max=80)])
	phone = StringField('Telefono', validators=[Optional(), Length(min=7, max=50)], default="+39 ")

	address = StringField('Indirizzo', validators=[Optional(), Length(min=3, max=150)])
	cap = StringField('CAP', validators=[Optional(), Length(min=5, max=5)])
	city = StringField('Città', validators=[Optional(), Length(min=3, max=55)])

	partner_id = SelectField("Seleziona Organizzazione", validators=[DataRequired("Campo obbligatorio!")])

	vat_number = StringField(
		'P. IVA', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	fiscal_code = StringField(
		'C.F.', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PARTNER_SITE: {self.site}>'

	def __str__(self):
		return f'<PARTNER_SITE: {self.site}>'

	def validate_site(self, field):  # noqa
		"""Verifica presenza organization nella tabella del DB."""
		if field.data.strip().replace('  ', ' ').lower() in list_partner_sites():
			raise ValidationError("Sito già presente in tabella.")

	@classmethod
	def update(cls, obj):
		# Instantiate the form
		form = cls()
		form.site.data = obj.site

		form.active.data = obj.active
		form.site_type.data = obj.site_type

		form.client.data = obj.client
		form.supplier.data = obj.supplier
		form.partner.data = obj.partner

		form.email.data = obj.email
		form.pec.data = obj.pec if obj.pec else None
		form.phone.data = obj.phone if obj.phone else None

		form.address.data = obj.address if obj.address else None
		form.cap.data = obj.cap if obj.cap else None
		form.city.data = obj.city if obj.city else None

		# Update the choices
		form.partner_id.choices = list_partners()

		form.vat_number.data = obj.vat_number
		form.fiscal_code.data = obj.fiscal_code
		form.sdi_code.data = obj.sdi_code if obj.sdi_code else None

		form.note.data = obj.note if obj.note else None
		return form

	def to_dict(self):
		"""Converte form in dict."""

		return {
			'site': self.site.data.strip().replace('  ', ' '),

			'active': status_true_false(self.active.data) if self.active.data else False,
			'site_type': self.site_type.data,

			'client': status_true_false(self.client.data) if self.client.data else False,
			'supplier': status_true_false(self.supplier.data) if self.supplier.data else False,
			'partner': status_true_false(self.partner.data) if self.partner.data else False,

			'email': self.email.data.strip().replace(" ", ""),
			'pec': not_empty(self.pec.data.strip().replace(" ", "")),
			'phone': not_empty(self.phone.data.strip()),

			'address': not_empty(self.address.data.strip()),
			'cap': not_empty(self.cap.data.strip()),
			'city': not_empty(self.city.data.strip()),
			'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

			'partner_id': self.partner_id.data.split(' - ')[0],

			'vat_number': self.vat_number.data,
			'fiscal_code': self.fiscal_code.data,
			'sdi_code': not_empty(self.sdi_code.data),

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
