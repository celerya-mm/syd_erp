from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import Length, Optional, DataRequired

from app.app import db
from app.support_lists import list_currency, list_um, list_item_categories

list_item_categories.sort()


def list_items(p_id=None, upd=None):
	from app.orders.items.models import Item

	_list = ["-"]
	try:
		if p_id:
			records = Item.query.filter_by(supplier_id=int(p_id)).order_by(Item.item_code.asc()).all()
		else:
			records = Item.query.order_by(Item.item_code.asc()).all()

		for r in records:
			if upd:
				_list.append(r.item_code)
			else:
				_list.append(f"{r.item_code} - {r.item_description}")

	except Exception as err:
		print('ERROR_LIST_ITEMS:', err)
		pass

	db.session.close()
	return _list


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.order_by(Partner.id.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print('ERROR_LIST_PARTNERS:', err)
		pass

	db.session.close()
	return _list


def list_partner_sites(p_id=None):
	from app.organizations.partner_sites.models import PartnerSite

	_list = ["-"]
	try:
		if p_id:
			records = PartnerSite.query.filter_by(partner_id=p_id).order_by(PartnerSite.id.asc()).all()
		else:
			records = PartnerSite.query.order_by(PartnerSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.site}")

	except Exception as err:
		print('ERROR_LIST_PARTNER_SITES:', err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


class FormOdaRowCreate(FlaskForm):
	"""Form per creare un Articolo."""
	item_code = SelectField('Codice Articolo', choices=list_items)

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ODA_ROW_FORM_CREATE: [ {self.item_code} ]>'

	def __str__(self):
		return f'<ODA_ROW_FORM_CREATE: [ {self.item_code} ]>'

	@classmethod
	def new(cls, p_id=None):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.item_code.choices = list_items(p_id)
		return form


class FormOdaRowUpdate(FlaskForm):
	"""Form per creare un Articolo."""
	item_code = SelectField('Codice Articolo', choices=list_items)
	item_code_supplier = StringField('Cod. F.', validators=[Optional(), Length(max=50)])

	item_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"), Length(max=500)])
	item_category = SelectField('Categoria', choices=list_item_categories)

	item_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	item_price_discount = DecimalField('Sconto %', validators=[Optional()], places=2)
	item_currency = SelectField('Valuta', choices=list_currency)

	item_amount = DecimalField('Prezzo', validators=[Optional()], places=2)

	oda_id = IntegerField("Oda", validators=[DataRequired("Campo obbligatorio!")])

	item_quantity = DecimalField('Q.', validators=[Optional()])
	item_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()])

	supplier_id = IntegerField("Fornitore", validators=[DataRequired("Campo obbligatorio!")])
	supplier_site_id = SelectField("Sito F.", validators=[Optional()])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ODA_ROW_FORM_UPDATE: [ {self.item_code} ] - {self.item_description}>'

	def __str__(self):
		return f'<ODA_ROW_FORM_UPDATE: [ {self.item_code} ] - {self.item_description}>'

	@classmethod
	def update(cls, obj, p_id=None):
		# Instantiate the form
		form = cls()

		form.item_code.data = obj.item_code
		form.item_code_supplier.data = obj.item_code_supplier or None

		form.item_description.data = obj.item_description
		form.item_category.data = obj.item_category

		form.item_price.data = obj.item_price
		form.item_price_discount.data = obj.item_price_discount or None
		form.item_currency.data = obj.item_currency or None

		form.item_quantity.data = obj.item_quantity or None
		form.item_quantity_um.data = obj.item_quantity_um or None

		form.oda_id.data = obj.oda_id

		form.supplier_id.data = obj.supplier_id

		# Update the choices
		form.item_code.choices = list_items(p_id, upd=True)
		form.supplier_site_id.choices = list_partner_sites(p_id)

		form.note.data = obj.note or None

		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.supplier_site_id.data and self.supplier_site_id.data not in ['', '-']:
			supplier_site_id = self.supplier_site_id.data.split(' - ')[0]
		else:
			supplier_site_id = None

		return {
			'item_code': self.item_code.data.split(' - ')[0],
			'item_code_supplier': not_empty(self.item_code_supplier.data.strip().replace('  ', ' ')),

			'item_description': not_empty(self.item_description.data.strip().replace('  ', ' ')),
			'item_category': self.item_category.data,

			'item_price': float(self.item_price.data),
			'item_price_discount': float(self.item_price_discount.data) if self.item_price_discount.data else None,
			'item_currency': self.item_currency.data,

			'item_quantity': not_empty(float(self.item_quantity.data)),
			'item_quantity_um': not_empty(self.item_quantity_um.data),

			'supplier_id': self.supplier_id.data,
			'supplier_site_id': supplier_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
