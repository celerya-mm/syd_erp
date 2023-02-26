from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.app import db, session
from .models import PlantSite
from app.functions import mount_full_address, not_empty, status_true_false, site_type


def list_plant_sites():
	try:
		records = PlantSite.query.all()
		if 'plant_site_id' in session.keys():
			_list = [x.to_dict() for x in records if x.id != session['plant_site_id']]
		else:
			_list = [x.to_dict() for x in records]

		_plant = [d["organization"] for d in _list]
		_email = [d["email"] for d in _list]
		_pec = [d["email"] for d in _list]
		_vat = [d["vat_number"] for d in _list]
		_sdi_code = [d["sdi_code"] for d in _list]

		db.session.close()

		_plant.sort()
		_email.sort()
		_pec.sort()
		_vat.sort()
		_sdi_code.sort()

		return _plant, _email, _pec, _vat, _sdi_code
	except Exception as err:
		print('ERROR_LIST_PLANT_SITES', err)
		return [], [], [], [], []


def list_plants():
	from app.organizations.plant.models import Plant
	_list = ["-"]
	try:
		records = Plant.query.all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")
	except Exception as err:
		print('ERROR_LIST_PLANTS', err)
		pass

	db.session.close()
	_list.sort()
	return _list


class FormPlantSite(FlaskForm):
	"""Form per creare un Sito sotto l'organizzazione."""
	organization = StringField('Rag. Sociale', validators=[DataRequired("Campo obbligatorio!"), Length(min=5, max=80)])

	active = BooleanField('Stato', false_values=(False, 0))
	site_type = SelectField("Seleziona Tipo", validators=[DataRequired("Campo obbligatorio!")], choices=site_type)

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	pec = EmailField('pec', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80), Optional()])
	phone = StringField('Telefono', validators=[Length(min=7, max=50), Optional()], default="+39 ")

	address = StringField('Indirizzo', validators=[Length(min=3, max=150), Optional()])
	cap = StringField('CAP', validators=[Length(min=5, max=5), Optional()])
	city = StringField('Città', validators=[Length(min=3, max=55), Optional()])

	plant_id = SelectField("Sede Legale")

	vat_number = StringField(
		'P. IVA', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	fiscal_code = StringField(
		'C.F.', validators=[DataRequired("Campo obbligatorio!"), Length(min=13, max=13)], default='IT'
	)
	sdi_code = StringField('SDI', validators=[Optional(), Length(min=7, max=7)])

	note = TextAreaField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<PLANT_SITE: {self.organization}>'

	def __str__(self):
		return f'<PLANT_SITE: {self.organization}>'

	@classmethod
	def new(cls):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.plant_id.choices = list_plants()
		return form

	@classmethod
	def update(cls, obj):
		# Instantiate the form
		form = cls()
		form.organization.data = obj.organization

		form.active.data = obj.active
		form.site_type.data = obj.site_type

		form.email.data = obj.email
		form.pec.data = obj.pec
		form.phone.data = obj.phone

		form.address.data = obj.address
		form.cap.data = obj.cap
		form.city.data = obj.city

		form.vat_number.data = obj.vat_number
		form.fiscal_code.data = obj.fiscal_code
		form.sdi_code.data = obj.sdi_code

		# Update the choices
		form.plant_id.choices = list_plants()

		form.note.data = obj.note
		return form

	def validate_organization(self, field):  # noqa
		"""Verifica presenza sito nella tabella del DB."""
		if field.data.strip() in list_plants()[0]:
			raise ValidationError("Sito già presente in tabella.")

	def to_dict(self):
		"""Converte form in dict."""

		return {
			'organization': self.organization.data.strip().replace("  ", " "),

			'active': status_true_false(self.active.data),
			'site_type': self.site_type.data,

			'email': self.email.data.strip().replace(" ", ""),
			'pec': self.pec.data.strip().replace(" ", ""),
			'phone': not_empty(self.phone.data.strip()),

			'address': not_empty(self.address.data.strip()),
			'cap': not_empty(self.cap.data.strip()),
			'city': not_empty(self.city.data.strip()),
			'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

			'plant_id': self.plant_id.data.split(' - ')[0],

			'vat_number': self.vat_number.data,
			'fiscal_code': self.fiscal_code.data,
			'sdi_code': not_empty(self.sdi_code.data),

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
