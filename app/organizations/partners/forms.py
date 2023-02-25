from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.app import db, session
from .models import Partner
from app.functions import mount_full_address, not_empty, status_true_false, site_type, list_payments


def list_partners():
	try:
		records = Partner.query.all()
		if 'partner_id' in session.keys():
			_list = [x.to_dict() for x in records if x.id != session['partner_id']]
		else:
			_list = [x.to_dict() for x in records]

		_partner = [d["organization"].lower() for d in _list]
		_email = [d["email"].lower() for d in _list]
		_pec = [d["email"].lower() for d in _list]
		_vat = [d["vat_number"] for d in _list]
		_sdi_code = [d["sdi_code"].lower() for d in _list]

		db.session.close()
		return _partner, _email, _pec, _vat, _sdi_code
	except Exception as err:
		print('ERROR_LIST_PARTNERS', err)
		return [], [], [], [], []


class FormPartner(FlaskForm):
	"""Form per creare un Partner."""
	organization = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	active = BooleanField('Stato', false_values=(False, 0))
	site_type = SelectField("Seleziona Tipo", validators=[DataRequired("Campo obbligatorio!")], choices=site_type)

	client = BooleanField('C', false_values=(False, 0))
	supplier = BooleanField('F', false_values=(False, 0))
	partner = BooleanField('P', false_values=(False, 0))

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	pec = EmailField('pec', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField(
		'Telefono', validators=[DataRequired("Campo obbligatorio!"), Length(min=7, max=25)], default="+39 ")

	address = StringField('Indirizzo', validators=[Optional(), Length(min=3, max=150)])
	cap = StringField('CAP', validators=[Optional(), Length(min=5, max=5)])
	city = StringField('Città', validators=[Optional(), Length(min=3, max=55)])

	vat_number = StringField(
		'P. IVA', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	fiscal_code = StringField(
		'C.F.', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	payment_condition = SelectField("Cond. Pagamento", validators=[Optional()], choices=list_payments)
	iban = StringField('IBAN', validators=[Optional(), Length(min=27, max=27)], default='IT')
	swift = StringField('SWIFT', validators=[Optional(), Length(min=12, max=12)])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PARTNER: {self.organization}>'

	def __str__(self):
		return f'<PARTNER: {self.organization}>'

	def validate_organization(self, field):  # noqa
		"""Verifica presenza organization nella tabella del DB."""
		if field.data.strip().lower() in list_partners()[0]:
			raise ValidationError("Organizzazione già presente in tabella partners.")

	def validate_email(self, field):  # noqa
		"""Verifica email già assegnata a partner nella tabella del DB."""
		if field.data.strip().lower() in list_partners()[1]:
			raise ValidationError("Email già assegnata in tabella partners.")

	def validate_pec(self, field):  # noqa
		"""Verifica pec già assegnata a partner nella tabella del DB."""
		if field.data.strip().lower() in list_partners()[2]:
			raise ValidationError("Pec già assegnata in tabella partners.")

	def validate_vat_number(self, field):  # noqa
		"""Verifica P.IVA già assegnata a partner nella tabella del DB."""
		if field.data.strip() in list_partners()[3]:
			raise ValidationError("P.IVA già assegnata in tabella partners.")

	def validate_sdi_code(self, field):  # noqa
		"""Verifica SDI già assegnata a partner nella tabella del DB."""
		if field.data.strip().lower() in list_partners()[4]:
			raise ValidationError("SDI Code già assegnato in tabella partners.")

	def to_dict(self):
		"""Converte form in dict."""

		return {
			'organization': self.organization.data.strip().replace('  ', ' '),

			'active': self.active.data,
			'site_type': self.site_type.data,

			'client': status_true_false(self.client.data) if self.client else False,
			'supplier': status_true_false(self.supplier.data) if self.supplier else False,
			'partner': status_true_false(self.partner.data) if self.partner else False,

			'email': self.email.data.strip().replace(" ", ""),
			'pec': self.pec.data.strip().replace(" ", ""),
			'phone': self.phone.data.strip(),

			'address': not_empty(self.address.data.strip()),
			'cap': not_empty(self.cap.data.strip()),
			'city': not_empty(self.city.data.strip()),
			'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

			'vat_number': self.vat_number.data,
			'fiscal_code': self.fiscal_code.data,
			'sdi_code': not_empty(self.sdi_code.data),

			'payment_condition': self.payment_condition.data if self.payment_condition.data else None,
			'iban': self.iban.data if self.iban.data else None,
			'swift': self.swift.data if self.swift.data else None,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
