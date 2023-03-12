from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db
from app.support_lists import list_currency, list_payments, list_order_status, list_item_categories

list_item_categories.sort()


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.filter_by(supplier=True).order_by(Partner.id.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print('ERROR_LIST_PARTNERS', err)
		pass

	db.session.close()
	return _list


def list_partner_sites(spl_id=None):
	from app.organizations.partner_sites.models import PartnerSite

	_list = ["-"]
	try:
		if spl_id:
			records = PartnerSite.query.filter_by(partner_id=spl_id, supplier=True).order_by(PartnerSite.id.asc()).all()
		else:
			records = PartnerSite.query.filter_by(supplier=True).order_by(PartnerSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.site}")

	except Exception as err:
		print('ERROR_LIST_PARTNER_SITES', err)
		pass

	db.session.close()
	return _list


def list_plants():
	from app.organizations.plants.models import Plant

	_list = ["-"]
	try:
		records = Plant.query.order_by(Plant.id.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print('ERROR_LIST_PLANTS', err)
		pass

	db.session.close()
	return _list


def list_plant_sites(pl_id=None):
	from app.organizations.plant_sites.models import PlantSite

	_list = ["-"]
	try:
		if pl_id:
			records = PlantSite.query.filter_by(plant_id=pl_id).order_by(PlantSite.id.asc()).all()
		else:
			records = PlantSite.query.order_by(PlantSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print(err)
		pass

	db.session.close()
	return _list


class FormOda(FlaskForm):
	"""Form per creare un Articolo."""
	oda_number = StringField('ODA', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])
	oda_date = DateField('Data', validators=[DataRequired("Campo obbligatorio!")])
	oda_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"), Length(max=255)])
	oda_category = SelectField('Categoria', choices=list_item_categories)

	oda_delivery_date = DateField('Data Consegna', validators=[DataRequired("Campo obbligatorio!")])
	oda_currency = SelectField(
		'Valuta', choices=list_currency, default='€', validators=[DataRequired("Campo obbligatorio!")])
	oda_payment = SelectField(
		'Pagamento', choices=list_payments, default='BB + 60gg DFFM', validators=[DataRequired("Campo obbligatorio!")])
	oda_status = SelectField(
		'Stato', choices=list_order_status, default='Lavorazione', validators=[DataRequired("Campo obbligatorio!")])

	plant_id = SelectField('Sede Legale', validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField('Sede Consegna', validators=[DataRequired("Campo obbligatorio!")])

	supplier_offer = StringField('Offerta', validators=[Optional(), Length(max=20)])
	supplier_offer_date = DateField('Data Offerta', validators=[Optional()])
	supplier_invoice = StringField('Fattura', validators=[Optional(), Length(max=50)])
	supplier_invoice_date = DateField('Data Fattura', validators=[Optional()])

	supplier_id = SelectField("Seleziona Fornitore")
	supplier_site_id = SelectField("Seleziona Sito Fornitore")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ODA_FORM: [{self.oda_number}] - {self.oda_date}>'

	def __str__(self):
		return f'<ODA_FORM: [{self.oda_number}] - {self.oda_date}>'

	@classmethod
	def new(cls, pl_id=None, spl_id=None):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites(pl_id)
		form.supplier_id.choices = list_partners()
		form.supplier_site_id.choices = list_partner_sites(spl_id)
		return form

	@classmethod
	def update(cls, obj, pl_id=None, spl_id=None):
		# Instantiate the form
		form = cls()
		form.oda_number.data = obj.oda_number
		form.oda_date.data = obj.oda_date
		form.oda_description.data = obj.oda_description
		form.oda_category.data = obj.oda_category

		form.oda_delivery_date.data = obj.oda_delivery_date
		form.oda_currency.data = obj.oda_currency
		form.oda_payment.data = obj.oda_payment
		form.oda_status.data = obj.oda_status

		form.supplier_offer.data = obj.supplier_offer if obj.supplier_offer else None
		form.supplier_offer_date.data = obj.supplier_offer_date if obj.supplier_offer_date else None
		form.supplier_invoice.data = obj.supplier_invoice if obj.supplier_invoice else None
		form.supplier_invoice_date.data = obj.supplier_invoice_date if obj.supplier_invoice_date else None

		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites(pl_id)

		form.supplier_id.choices = list_partners()
		form.supplier_site_id.choices = list_partner_sites(spl_id)

		form.note.data = obj.note
		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty, date_to_str

		if self.plant_site_id.data and self.plant_site_id.data != '-':
			plant_site_id = int(self.plant_site_id.data.split(' - ')[0])
		else:
			plant_site_id = None

		if self.supplier_site_id.data and self.supplier_site_id.data != '-':
			supplier_site_id = int(self.supplier_site_id.data.split(' - ')[0])
		else:
			supplier_site_id = None

		return {
			'oda_number': self.oda_number.data,
			'oda_date': date_to_str(self.oda_date.data),
			'oda_year': self.oda_date.data.year,

			'oda_description': self.oda_description.data.strip().replace('  ', ' '),
			'oda_category': self.oda_category.data,

			'oda_delivery_date': date_to_str(self.oda_delivery_date.data),
			'oda_currency': self.oda_currency.data,
			'oda_payment': not_empty(self.oda_payment.data),
			'oda_status': not_empty(self.oda_status.data),

			'plant_id': self.plant_id.data.split(' - ')[0],
			'plant_site_id': plant_site_id,

			'supplier_offer': not_empty(self.supplier_offer.data.strip().replace(' ', '')),
			'supplier_offer_date': date_to_str(self.supplier_offer_date.data),
			'supplier_invoice': not_empty(self.supplier_invoice.data.strip().replace('  ', ' ')),
			'supplier_invoice_date': date_to_str(self.supplier_invoice_date.data),

			'supplier_id': self.supplier_id.data.split(' - ')[0],
			'supplier_site_id': supplier_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
