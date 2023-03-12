from datetime import datetime, timedelta, date

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db
from app.support_lists import list_currency, list_payments, list_invoice_status, list_activity_categories

list_activity_categories.sort()


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.filter_by(client=True).order_by(Partner.id.asc()).all()
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
			records = PartnerSite.query.filter_by(partner_id=spl_id, client=True).order_by(PartnerSite.id.asc()).all()
		else:
			records = PartnerSite.query.filter_by(client=True).order_by(PartnerSite.id.asc()).all()

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


class FormInvoice(FlaskForm):
	"""Form per creare un Articolo."""
	invoice_number = StringField('Fattura', validators=[DataRequired("Campo obbligatorio!"), Length(min=8, max=8)])
	invoice_date = DateField('Data', validators=[DataRequired("Campo obbligatorio!")])

	invoice_description = TextAreaField('Descrizione',
										validators=[DataRequired("Campo obbligatorio!"), Length(max=255)])
	invoice_category = SelectField('Categoria', choices=list_activity_categories)

	invoice_currency = SelectField(
		'Valuta', choices=list_currency, default='€', validators=[DataRequired("Campo obbligatorio!")])
	invoice_payment = SelectField(
		'Pagamento', choices=list_payments, default='BB + 60gg DFFM', validators=[DataRequired("Campo obbligatorio!")])
	invoice_status = SelectField(
		'Stato', choices=list_invoice_status, default='Lavorazione', validators=[DataRequired("Campo obbligatorio!")])

	plant_id = SelectField('Sede Legale', validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField('Sede Operativa', validators=[DataRequired("Campo obbligatorio!")])

	client_order_nr = StringField('ODA Cliente', validators=[Optional(), Length(max=20)])
	client_order_date = DateField('Data ODA', validators=[Optional()])

	client_id = SelectField("Seleziona Cliente")
	client_site_id = SelectField("Seleziona Sito Cliente")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<INVOICE_FORM: [{self.invoice_number}] - {self.invoice_description}>'

	def __str__(self):
		return f'<INVOICE_FORM: [{self.invoice_number}] - {self.invoice_description}>'

	@classmethod
	def new(cls, pl_id=None, spl_id=None):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites(pl_id)
		form.client_id.choices = list_partners()
		form.client_site_id.choices = list_partner_sites(spl_id)
		return form

	@classmethod
	def update(cls, obj, pl_id=None, spl_id=None):
		# Instantiate the form
		form = cls()
		form.invoice_number.data = obj.invoice_number
		form.invoice_date.data = obj.invoice_date

		form.invoice_description.data = obj.invoice_description
		form.invoice_category.data = obj.invoice_category

		form.invoice_currency.data = obj.invoice_currency
		form.invoice_payment.data = obj.invoice_payment
		form.invoice_status.data = obj.invoice_status

		form.client_order_nr.data = obj.client_order_nr if obj.client_order_nr else None
		form.client_order_date.data = obj.client_order_date if obj.client_order_date else None

		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites(pl_id)

		form.client_id.choices = list_partners()
		form.client_site_id.choices = list_partner_sites(spl_id)

		form.note.data = obj.note
		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty, date_to_str

		if self.plant_site_id.data and self.plant_site_id.data != '-':
			plant_site_id = int(self.plant_site_id.data.split(' - ')[0])
		else:
			plant_site_id = None

		if self.client_site_id.data and self.client_site_id.data != '-':
			client_site_id = int(self.client_site_id.data.split(' - ')[0])
		else:
			client_site_id = None

		if self.invoice_payment.data:
			# calcola l'ultimo giorno del mese della data di fattura
			fine_mese = (self.invoice_date.data + timedelta(days=32)).replace(day=1) - timedelta(days=1)

			if '30' in self.invoice_payment.data:
				expiration = fine_mese + timedelta(days=30)
			elif '60' in self.invoice_payment.data:
				expiration = fine_mese + timedelta(days=60)
			elif '90' in self.invoice_payment.data:
				expiration = fine_mese + timedelta(days=90)
			else:
				expiration = self.invoice_date.data
		else:
			expiration = None

		if expiration not in [None, '']:
			if self.invoice_status.data not in ['Pagata_OK', 'Pagata_Ritardo']:
				expired = bool(expiration < date.today())
			else:
				expired = False
		else:
			expired = False

		return {
			'invoice_number': self.invoice_number.data,
			'invoice_date': date_to_str(self.invoice_date.data),
			'invoice_year': self.invoice_date.data.year,

			'invoice_description': self.invoice_description.data.strip().replace('  ', ' '),
			'invoice_category': self.invoice_category.data,

			'invoice_currency': self.invoice_currency.data,
			'invoice_payment': not_empty(self.invoice_payment.data),
			'invoice_status': not_empty(self.invoice_status.data),

			'invoice_expiration_date': expiration,
			'invoice_expired': expired,

			'plant_id': self.plant_id.data.split(' - ')[0],
			'plant_site_id': plant_site_id,

			'client_order_nr': not_empty(self.client_order_nr.data.strip().replace(' ', '')),
			'client_order_date': date_to_str(self.client_order_date.data),

			'client_id': self.client_id.data.split(' - ')[0],
			'client_site_id': client_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
