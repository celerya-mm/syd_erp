from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db
from app.support_lists import list_currency, list_um, list_activity_categories

list_activity_categories.sort()


def list_plant_sites(p_id=None):
	from app.organizations.plant_sites.models import PlantSite

	_list = ["-"]
	try:
		if p_id:
			records = PlantSite.query.filter_by(plant_id=p_id, active=True).order_by(PlantSite.id.asc()).all()
		else:
			records = PlantSite.query.filter_by(active=True).order_by(PlantSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print('ERROR_LIST_PLANT_SITES:', err)
		pass

	db.session.close()
	return _list


class FormActivity(FlaskForm):
	"""Form per creare un Articolo."""
	activity_code = StringField('Cod. Attività', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])

	activity_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"),
																	Length(max=500)])
	activity_category = SelectField('Categoria', choices=list_activity_categories)

	activity_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	activity_currency = SelectField('Valuta', choices=list_currency)

	activity_quantity = DecimalField('Q. min.', validators=[Optional()])
	activity_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()], default='unit')

	activity_estimated_time = DecimalField('h prev.', validators=[Optional()])

	plant_site_id = SelectField("Seleziona Sito")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ACTIVITY_FORM: [{self.activity_code}] - {self.activity_description}>'

	def __str__(self):
		return f'<ACTIVITY_FORM: [{self.activity_code}] - {self.activity_description}>'

	@classmethod
	def new(cls, p_id=None):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.plant_site_id.choices = list_plant_sites(p_id)
		return form

	@classmethod
	def update(cls, obj, p_id=None):
		# Instantiate the form
		form = cls()
		form.activity_code.data = obj.activity_code

		form.activity_description.data = obj.activity_description
		form.activity_category.data = obj.activity_category

		form.activity_price.data = obj.activity_price
		form.activity_currency.data = obj.activity_currency

		form.activity_quantity.data = obj.activity_quantity if obj.activity_quantity else None
		form.activity_quantity_um.data = obj.activity_quantity_um if obj.activity_quantity_um else None

		form.activity_estimated_time.data = obj.activity_estimated_time if obj.activity_estimated_time else None

		# Update the choices
		form.plant_site_id.choices = list_plant_sites(p_id)

		form.note.data = obj.note if obj.note else None
		return form

	def to_dict_new(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.plant_site_id.data and self.plant_site_id.data not in ['', '-']:
			plant_site_id = self.plant_site_id.data.split(' - ')[0]
		else:
			plant_site_id = None

		return {
			'activity_code': self.activity_code.data,

			'activity_description': self.activity_description.data.strip().replace('  ', ' '),
			'activity_category': self.activity_category.data,

			'activity_price': self.activity_price.data,
			'activity_currency': self.activity_currency.data,

			'activity_quantity': not_empty(self.activity_quantity.data),
			'activity_quantity_um': not_empty(self.activity_quantity_um.data),

			'activity_estimated_time': not_empty(self.activity_estimated_time.data),

			'plant_site_id': plant_site_id,

			'note': not_empty(self.note.data.strip())
		}

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.plant_site_id.data and self.plant_site_id.data not in ['', '-']:
			plant_site_id = self.plant_site_id.data.split(' - ')[0]
		else:
			plant_site_id = None

		return {
			'activity_code': self.activity_code.data,

			'activity_description': self.activity_description.data.strip().replace('  ', ' '),
			'activity_category': self.activity_category.data,

			'activity_price': self.activity_price.data,
			'activity_currency': not_empty(self.activity_currency.data),

			'activity_quantity': not_empty(self.activity_quantity.data),
			'activity_quantity_um': not_empty(self.activity_quantity_um.data),

			'activity_estimated_time': not_empty(self.activity_estimated_time.data),

			'plant_site_id': plant_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
