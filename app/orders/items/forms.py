from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db, session
from app.functions import list_currency


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")
	except Exception as err:
		print(err)
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
		print('EXTRACT_LIST:', err)
		pass

	db.session.close()
	return _list


list_um = ['kg', 'pz', 'unit']


class FormItem(FlaskForm):
	"""Form per creare un Articolo."""
	item_code = StringField('Cod. ITM', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])
	item_code_supplier = StringField('Cod. F.', validators=[Optional(), Length(max=50)])

	item_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"), Length(max=500)])

	item_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	item_price_discount = DecimalField('Sconto %', validators=[Optional()], places=2)
	item_currency = SelectField('Valuta', choices=list_currency)

	item_quantity_min = DecimalField('Q. min.', validators=[Optional()])
	item_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()])

	supplier_id = SelectField("Seleziona Fornitore")
	supplier_site_id = SelectField("Seleziona Sito Fornitore")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	@classmethod
	def new(cls):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.supplier_id.choices = list_partners()
		form.supplier_site_id.choices = list_partner_sites()
		return form

	@classmethod
	def update(cls, obj):
		# Instantiate the form
		form = cls()
		form.item_code.data = obj.item_code
		form.item_code_supplier.data = obj.item_code_supplier if obj.item_code_supplier else None

		form.item_description.data = obj.item_description

		form.item_price.data = obj.item_price
		form.item_price_discount.data = obj.item_price_discount if obj.item_price_discount else None
		form.item_currency.data = obj.item_currency

		form.item_quantity_min.data = obj.item_quantity_min if obj.item_quantity_min else None
		form.item_quantity_um.data = obj.item_quantity_um if obj.item_quantity_um else None

		# Update the choices
		form.supplier_id.choices = list_partners()
		form.supplier_site_id.choices = list_partner_sites()

		form.note.data = obj.note if obj.note else None
		return form

	def to_dict_new(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.supplier_site_id.data and self.supplier_site_id.data not in ['', '-']:
			supplier_site_id = self.supplier_site_id.data.split(' - ')[0]
		else:
			supplier_site_id = None

		return {
			'item_code': self.item_code.data,
			'item_code_supplier': not_empty(self.item_code_supplier.data.strip().replace('  ', ' ')),

			'item_description': self.item_description.data.strip().replace('  ', ' '),

			'item_price': self.item_price.data,
			'item_price_discount': not_empty(self.item_price_discount.data),
			'item_currency': self.item_currency.data,

			'item_quantity_min': not_empty(self.item_quantity_min.data),
			'item_quantity_um': not_empty(self.item_quantity_um.data),

			'supplier_id': self.supplier_id.data.split(' - ')[0],
			'supplier_site_id': supplier_site_id,

			'note': not_empty(self.note.data.strip())
		}

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.supplier_site_id.data and self.supplier_site_id.data not in ['', '-']:
			supplier_site_id = self.supplier_site_id.data.split(' - ')[0]
		else:
			supplier_site_id = None

		return {
			'item_code': self.item_code.data,
			'item_code_supplier': not_empty(self.item_code_supplier.data.strip().replace('  ', ' ')),

			'item_description': self.item_description.data.strip().replace('  ', ' '),

			'item_price': self.item_price.data,
			'item_price_discount': not_empty(self.item_price_discount.data),
			'item_currency': not_empty(self.item_currency.data),

			'item_quantity_min': not_empty(self.item_quantity_min.data),
			'item_quantity_um': not_empty(self.item_quantity_um.data),

			'supplier_id': self.supplier_id.data.split(' - ')[0],
			'supplier_site_id': supplier_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
