from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db


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
		records = PartnerSite.query.all()
		for r in records:
			# print("PARTNER_ID:", r.partner_id, supplier_id, r.partner_id == supplier_id)
			# if r.partner_id == supplier_id:
			_list.append(f"{r.id} - {r.site}")
	except Exception as err:
		print(err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


list_um = ['kg', 'pz', 'unit']


class FormItem(FlaskForm):
	"""Form per creare un Articolo."""
	item_code = StringField('Cod. Articolo', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])
	item_code_supplier = StringField('Cod. Fornitore', validators=[Length(max=50), Optional()])

	item_description = StringField('Descr. Articolo', validators=[DataRequired("Campo obbligatorio!"), Length(max=255)])

	item_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	item_price_discount = DecimalField('Sconto %', validators=[Optional()], places=2)

	item_quantity_min = IntegerField('Q. minima', validators=[Optional()])
	item_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()])

	supplier_id = SelectField("Seleziona Fornitore", choices=list_partners())
	supplier_site_id = SelectField("Seleziona Sito Fornitore", choices=list_partner_sites())

	note = StringField('Note', validators=[Length(max=255), Optional()])

	submit = SubmitField("SIGNUP")

	def __repr__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ITEM_FORM: [{self.item_code}] - {self.item_description}>'

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.supplier_site_id.data and self.supplier_site_id.data != '-':
			supplier_site_id = self.supplier_site_id.data.split(' - ')[0]
		else:
			supplier_site_id = None

		return {
			'item_code': self.item_code,
			'item_code_supplier': not_empty(self.item_code_supplier.data.strip().replace('  ', ' ')),

			'item_description': self.item_description.data.strip().replace('  ', ' '),

			'item_price': self.item_price.data,
			'item_price_discount': not_empty(self.item_price_discount.data),

			'item_quantity_min': not_empty(self.item_quantity_min.data),
			'item_quantity_um': not_empty(self.item_quantity_um.data),

			'supplier_id': self.supplier_id.data.split(' - ')[0],
			'supplier_site_id': supplier_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
