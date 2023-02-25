from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.app import session, db
from .models import Plant
from app.functions import mount_full_address, not_empty, status_true_false, site_type


def list_plants():
	try:
		records = Plant.query.all()
		if 'plant_id' in session.keys():
			_list = [x.to_dict() for x in records if x.id != session['plant_id']]
		else:
			_list = [x.to_dict() for x in records]

		_plant = [d["organization"] for d in _list]
		_email = [d["email"] for d in _list]
		_pec = [d["email"] for d in _list]
		_vat = [d["vat_number"] for d in _list]
		_sdi_code = [d["sdi_code"] for d in _list]

		db.session.close()
		return _plant, _email, _pec, _vat, _sdi_code
	except Exception as err:
		print('ERROR_LIST_PLANTS', err)
		return [], [], [], [], []


class FormPlant(FlaskForm):
	"""Form per creare un Partner."""
	organization = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	active = BooleanField('Stato', false_values=(False, 0))
	site_type = SelectField("Seleziona Tipo", validators=[Optional()], choices=site_type)

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
	fiscal_code = StringField('C.F.', validators=[Optional(), Length(min=13, max=13)], default='IT')
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PLANT: {self.organization}>'

	def __str__(self):
		return f'<PLANT: {self.organization}>'

	def validate_organization(self, field):  # noqa
		"""Verifica presenza organization nella tabella del DB."""
		if field.data.strip() in list_plants()[0]:
			raise ValidationError("Organizzazione già presente in tabella.")

	def validate_email(self, field):  # noqa
		"""Verifica email già assegnata nella tabella del DB."""
		if field.data.strip() in list_plants()[1]:
			raise ValidationError("Email già assegnata in tabella.")

	def validate_pec(self, field):  # noqa
		"""Verifica pec già assegnata nella tabella del DB."""
		if field.data.strip() in list_plants()[2]:
			raise ValidationError("Pec già assegnata in tabella.")

	def validate_vat_number(self, field):  # noqa
		"""Verifica P.IVA già assegnata nella tabella del DB."""
		if field.data.strip() in list_plants()[3]:
			raise ValidationError("P.IVA già assegnata in tabella.")

	def validate_sdi_code(self, field):  # noqa
		"""Verifica SDI già assegnata nella tabella del DB."""
		if field.data.strip() in list_plants()[4]:
			raise ValidationError("SDI Code già assegnato in tabella.")

	def to_dict(self):
		"""Converte form in dict."""

		return {
			'organization': self.organization.data.strip().replace("  ", " "),

			'active': status_true_false(self.active.data),
			'site_type': not_empty(self.site_type.data),

			'email': self.email.data.strip().replace(" ", ""),
			'pec': self.pec.data.strip().replace(" ", ""),
			'phone': self.phone.data.strip(),

			'address': not_empty(self.address.data.strip()),
			'cap': not_empty(self.cap.data.strip()),
			'city': not_empty(self.city.data.strip()),
			'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

			'vat_number': self.vat_number.data,
			'fiscal_code': not_empty(self.fiscal_code.data),
			'sdi_code': not_empty(self.sdi_code.data),

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
