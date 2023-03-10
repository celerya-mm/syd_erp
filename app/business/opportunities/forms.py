from datetime import datetime, date

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, DateField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, Optional

from app.app import db
from app.support_lists import list_opp_status, list_opp_categories

list_opp_categories.sort()
list_opp_status.sort()


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.order_by(Partner.id.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print('ERROR_LIST_PARTNERS', err)
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
		print('ERROR_LIST_PARTNER_SITES', err)
		pass

	db.session.close()
	return _list


def list_partner_contacts(p_id, s_id=None):
	from app.organizations.partner_contacts.models import PartnerContact

	_list = ["-"]
	try:
		if s_id:
			records = PartnerContact.query.filter_by(partner_site_id=s_id).order_by(PartnerContact.id.asc()).all()
		else:
			records = PartnerContact.query.filter_by(partner_id=p_id).order_by(PartnerContact.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.full_name}")

	except Exception as err:
		print('ERROR_LIST_PARTNER_CONTACTS', err)
		pass

	db.session.close()
	return _list


def list_plants():
	from app.organizations.plant.models import Plant

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


def list_plant_sites():
	from app.organizations.plant_site.models import PlantSite

	_list = ["-"]
	try:
		records = PlantSite.query.order_by(PlantSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.organization}")

	except Exception as err:
		print(err)
		pass

	db.session.close()
	return _list


def list_activities():
	from app.invoices.activities.models import Activity

	_list = ["-"]
	try:
		records = Activity.query.order_by(Activity.activity_code.asc()).all()
		for r in records:
			_list.append(f"{r.activity_code} - {r.activity_description}")

	except Exception as err:
		print('ERROR_LIST_ACTIVITIES', err)
		pass

	db.session.close()
	return _list


def list_users():
	from app.account.models import User

	_list = []
	try:
		records = User.query.order_by(User.full_name.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.full_name}")

	except Exception as err:
		print('ERROR_LIST_USERS', err)
		pass

	db.session.close()
	return _list


class FormOpportunity(FlaskForm):
	"""Form per creare un Articolo."""
	opp_activity = SelectField('Attività', choices=list_activities, validators=[DataRequired("Campo obbligatorio!")])
	opp_value = DecimalField('Valore', validators=[Optional()], places=2)

	opp_date = DateField('Data', validators=[DataRequired("Campo obbligatorio!")])
	opp_expiration_date = DateField('Scadenza', validators=[DataRequired("Campo obbligatorio!")])

	opp_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"), Length(max=500)])
	opp_category = SelectField('Categoria', choices=list_opp_categories)

	opp_accountable = SelectField('Responsabile', choices=list_users)

	opp_status = SelectField('Stato', choices=list_opp_status, validators=[DataRequired("Campo obbligatorio!")])

	plant_id = SelectField('Sede Legale', validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField('Sede Operativa', validators=[DataRequired("Campo obbligatorio!")])

	partner_id = SelectField("Seleziona partner")
	partner_site_id = SelectField("Seleziona Sito Partner")
	partner_contact_id = SelectField("Seleziona Referente")

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<OPPORTUNITY_FORM: [{self.opp_activity}] - {self.opp_status}>'

	def __str__(self):
		return f'<OPPORTUNITY_FORM: [{self.opp_activity}] - {self.opp_status}>'

	@classmethod
	def new(cls, p_id=None):
		# Instantiate the form
		form = cls()

		# Update the choices
		form.opp_activity.choices = list_activities()
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites()

		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites(p_id)
		form.partner_contact_id.choices = list_partner_contacts(p_id)
		return form

	@classmethod
	def update(cls, obj, p_id=None):
		# Instantiate the form
		form = cls()
		form.opp_value.data = obj.opp_value
		form.opp_date.data = obj.opp_date

		form.opp_description.data = obj.opp_description
		form.opp_category.data = obj.opp_category

		form.opp_accountable.data = obj.opp_accountable
		form.opp_status.data = obj.opp_status

		form.note.data = obj.note

		# Update the choices
		form.opp_activity.choices = list_activities()

		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites()

		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites(p_id)
		form.partner_contact_id.choices = list_partner_contacts(p_id)
		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty, date_to_str

		if self.plant_site_id.data and self.plant_site_id.data != '-':
			plant_site_id = int(self.plant_site_id.data.split(' - ')[0])
		else:
			plant_site_id = None

		if self.partner_site_id.data and self.partner_site_id.data != '-':
			partner_site_id = int(self.partner_site_id.data.split(' - ')[0])
		else:
			partner_site_id = None

		if self.opp_expiration_date.data not in [None, '']:
			if 'closed' not in self.opp_status.data.lower():
				expired = bool(self.opp_expiration_date.data < date.today())
			else:
				expired = False
		else:
			expired = False

		return {
			'opp_activity': self.opp_activity.data.split(' - ')[0],
			'opp_value': self.opp_value.data,

			'opp_date': date_to_str(self.opp_date.data),
			'opp_year': self.opp_date.data.year,

			'opp_description': self.opp_description.data.strip().replace('  ', ' '),
			'opp_category': self.opp_category.data,

			'opp_status': not_empty(self.opp_status.data),

			'opp_expiration_date': date_to_str(self.opp_expiration_date.data),
			'opp_expired': expired,

			'opp_accountable': self.opp_accountable.data,

			'plant_id': self.plant_id.data.split(' - ')[0],
			'plant_site_id': plant_site_id,

			'partner_id': self.partner_id.data.split(' - ')[0],
			'partner_site_id': partner_site_id,
			'partner_contact_id': self.partner_contact_id.data(' - ')[0],

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
