from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import Length, Optional, DataRequired

from app.app import db
from app.functions import list_currency, list_um


def list_activities(upd=None):
	from app.invoices.activities.models import Activity

	_list = ["-"]
	try:
		records = Activity.query.order_by(Activity.activity_code.asc()).all()
		for r in records:
			if upd:
				_list.append(r.activity_code)
			else:
				_list.append(f"{r.activity_code} - {r.activity_description}")
	except Exception as err:
		print('ERROR_LIST_ACTIVITIES:', err)
		pass

	db.session.close()
	return _list


def list_clients():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.filter_by(client=True).order_by(Partner.id.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")
	except Exception as err:
		print('ERROR_LIST_CLIENTS:', err)
		pass

	db.session.close()
	return _list


def list_client_sites(p_id=None):
	from app.organizations.partner_sites.models import PartnerSite

	_list = ["-"]
	try:
		if p_id:
			records = PartnerSite.query.filter_by(partner_id=p_id, client=True).order_by(PartnerSite.id.asc()).all()
		else:
			records = PartnerSite.query.order_by(PartnerSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.site}")
	except Exception as err:
		print('ERROR_LIST_CLIENT_SITES:', err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


class FormInvoiceRowCreate(FlaskForm):
	"""Form per creare una riga Fattura."""
	activity_code = SelectField('Codice Attività', choices=list_activities)

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<INVOICE_ROW_FORM_CREATE: [ {self.activity_code} ]>'

	def __str__(self):
		return f'<INVOICE_ROW_FORM_CREATE: [ {self.activity_code} ]>'

	@classmethod
	def new(cls, p_id=None):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.activity_code.choices = list_activities(p_id)
		return form


class FormInvoiceRowUpdate(FlaskForm):
	"""Form per aggiornare riga Fattura."""
	activity_code = SelectField('Codice Articolo', choices=list_activities)

	activity_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"),
																	Length(max=500)])

	activity_price = DecimalField('Prezzo', validators=[DataRequired("Campo obbligatorio!")], places=2)
	activity_price_discount = DecimalField('Sconto %', validators=[Optional()], places=2)
	activity_currency = SelectField('Valuta', choices=list_currency)

	activity_estimated_time = DecimalField('Impegno', validators=[Optional()], places=2)

	activity_amount = DecimalField('Totale', validators=[Optional()], places=2)

	invoice_id = IntegerField("Fattura", validators=[DataRequired("Campo obbligatorio!")])

	activity_quantity = DecimalField('Q.', validators=[Optional()])
	activity_quantity_um = SelectField('U.M.', choices=list_um, validators=[Optional()])

	client_id = IntegerField("Cliente", validators=[DataRequired("Campo obbligatorio!")])
	client_site_id = SelectField("Sito C.", validators=[Optional()])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<INVOICE_ROW_FORM_UPDATE: [ {self.activity_code} ] - {self.activity_description}>'

	def __str__(self):
		return f'<INVOICE_ROW_FORM_UPDATE: [ {self.activity_code} ] - {self.activity_description}>'

	@classmethod
	def update(cls, obj, p_id=None):
		# Instantiate the form
		form = cls()

		# Update the choices
		form.activity_code.choices = list_activities(upd=True)
		form.client_site_id.choices = list_client_sites(p_id)

		form.activity_code.data = obj.activity_code

		form.activity_description.data = obj.activity_description

		form.activity_price.data = obj.activity_price
		form.activity_price_discount.data = obj.activity_price_discount or None
		form.activity_currency.data = obj.activity_currency or None

		form.activity_quantity.data = obj.activity_quantity or None
		form.activity_quantity_um.data = obj.activity_quantity_um or None

		form.activity_estimated_time.data = obj.activity_estimated_time or None

		form.invoice_id.data = obj.invoice_id

		form.client_id.data = obj.client_id
		form.client_site_id.data = obj.client_site_id or None

		form.note.data = obj.note or None

		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty

		if self.client_site_id.data and self.client_site_id.data not in ['', '-']:
			client_site_id = self.client_site_id.data.split(' - ')[0]
		else:
			client_site_id = None

		return {
			'activity_code': self.activity_code.data.split(' - ')[0],

			'activity_description': not_empty(self.activity_description.data.strip().replace('  ', ' ')),

			'activity_price': float(self.activity_price.data),
			'activity_price_discount': float(self.activity_price_discount.data) if self.activity_price_discount.data
			else None,
			'activity_currency': self.activity_currency.data,

			'activity_quantity': not_empty(float(self.activity_quantity.data)),
			'activity_quantity_um': not_empty(self.activity_quantity_um.data),
			'activity_estimated_time':  not_empty(float(self.activity_estimated_time.data)),

			'client_id': self.client_id.data,
			'client_site_id': client_site_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
