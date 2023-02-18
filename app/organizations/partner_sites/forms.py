from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from config import db
from .models import PartnerSite
from app.functions import mount_full_address, not_empty, status_true_false


def list_partner_sites():
	try:
		records = PartnerSite.query.all()
		_list = [x.to_dict() for x in records]

		_partner = [d["site"] for d in _list]
		_email = [d["email"] for d in _list]
		_pec = [d["email"] for d in _list]
		_vat = [d["vat_number"] for d in _list]
		_sdi_code = [d["sdi_code"] for d in _list]

		db.session.close()
		return _partner, _email, _pec, _vat, _sdi_code
	except Exception as err:
		print(err)
		return [], [], [], [], []


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


class FormPartnerSiteCreate(FlaskForm):
	"""Form per creare un Partner."""
	site = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	client = BooleanField('Cliente', false_values=(False, 0))
	supplier = BooleanField('Fornitore', false_values=(False, 0))
	partner = BooleanField('Partner', false_values=(False, 0))

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	pec = EmailField('pec', validators=[Email(), Length(max=80), Optional()])
	phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()], default="+39 ")

	address = StringField('Indirizzo', validators=[Length(min=3, max=150), Optional()])
	cap = StringField('CAP', validators=[Length(min=5, max=5), Optional()])
	city = StringField('Città', validators=[Length(min=3, max=55), Optional()])

	partner_id = SelectField(
		"Seleziona Organizzazione", choices=list_partners(), validators=[DataRequired("Campo obbligatorio!")])

	vat_number = StringField(
		'P. IVA', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	fiscal_code = StringField(
		'C.F.', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PARTNER_SITE_CREATED: {self.site}>'

	def __str__(self):
		return f'<PARTNER_SITE_CREATED: {self.site}>'

	def validate_site(self, field):  # noqa
		"""Verifica presenza organization nella tabella del DB."""
		if field.data.strip() in list_partner_sites()[0]:
			raise ValidationError("Sito già presente in tabella partner_sites.")

	def validate_email(self, field):  # noqa
		"""Verifica email già assegnata a un sito nella tabella del DB."""
		if field.data.strip() in list_partner_sites()[1]:
			raise ValidationError("Email già assegnata in tabella partner_sites.")

	def validate_pec(self, field):  # noqa
		"""Verifica pec già assegnata a un sito nella tabella del DB."""
		if field.data.strip() in list_partner_sites()[2]:
			raise ValidationError("Pec già assegnata in tabella partner_sites.")

	def validate_vat_number(self, field):  # noqa
		"""Verifica P.IVA già assegnata a un sito nella tabella del DB."""
		if field.data.strip() in list_partner_sites()[3]:
			raise ValidationError("P.IVA già assegnata in tabella partner_sites.")

	def validate_sdi_code(self, field):  # noqa
		"""Verifica SDI già assegnata a un sito nella tabella del DB."""
		if field.data.strip() in list_partners()[4]:
			raise ValidationError("SDI Code già assegnato in tabella partner_sites.")


class FormPartnerSiteUpdate(FlaskForm):
	"""Form per creare un Partner."""
	site = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	client = BooleanField('Cliente')
	supplier = BooleanField('Fornitore')
	partner = BooleanField('Partner')

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	pec = EmailField('pec', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()], default="+39 ")

	address = StringField('Indirizzo', validators=[Length(min=3, max=150), Optional()])
	cap = StringField('CAP', validators=[Length(min=5, max=5), Optional()])
	city = StringField('Città', validators=[Length(min=3, max=55), Optional()])

	partner_id = SelectField(
		"Seleziona Partner", choices=list_partners(), validators=[DataRequired("Campo obbligatorio!")])

	vat_number = StringField(
		'P. IVA', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	fiscal_code = StringField(
		'C.F.', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PARTNER_SITE_UPDATED: {self.site}>'

	def __str__(self):
		return f'<PARTNER_SITE_UPDATED: {self.site}>'

	def to_dict(self):
		"""Converte form in dict."""

		return {
			'site': self.site.data.strip(),

			'client': status_true_false(self.client.data),
			'supplier': status_true_false(self.supplier.data),
			'partner': status_true_false(self.partner.data),

			'email': self.email.data.strip().replace(" ", ""),
			'pec': self.pec.data.strip().replace(" ", ""),
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
