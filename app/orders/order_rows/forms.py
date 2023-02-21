from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Optional

from app.functions import list_currency

list_um = ['kg', 'pz', 'unit']


class FormOdaRow(FlaskForm):
	"""Form per creare un Articolo."""
	item_code = StringField('Cod. ITM', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])
	item_code_supplier = StringField('Cod. F.', validators=[Length(max=50), Optional()])

	item_description = StringField('Descrizione', validators=[DataRequired("Campo obbligatorio!"), Length(max=255)])

	item_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	item_price_discount = DecimalField('Sconto %', validators=[Optional()], places=2)
	item_currency = SelectField('Valuta', choices=list_currency)

	item_quantity = IntegerField('Q. minima', validators=[Optional()])
	item_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()])

	supplier_id = IntegerField("F.", validators=[DataRequired("Campo obbligatorio!")])
	supplier_site_id = IntegerField("Sito F.", validators=[DataRequired("Campo obbligatorio!")])

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		return {
			'item_code': self.item_code.data,
			'item_code_supplier': not_empty(self.item_code_supplier.data.strip().replace('  ', ' ')),

			'item_description': self.item_description.data.strip().replace('  ', ' '),

			'item_price': self.item_price.data,
			'item_price_discount': not_empty(self.item_price_discount.data),
			'item_currency': self.item_currency.data,

			'item_quantity': not_empty(self.item_quantity.data),
			'item_quantity_um': not_empty(self.item_quantity_um.data),

			'supplier_id': self.supplier_id.data.split(' - ')[0],
			'supplier_site_id': self.supplier_site_id.data.split(' - ')[0] if self.supplier_site_id.data else None,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
