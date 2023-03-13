from datetime import datetime, date

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField, DecimalField, TextAreaField, DateField
from wtforms.validators import Length, Optional, DataRequired

from app.app import db, session
from app.support_lists import list_opp_categories

list_opp_categories.sort()


def list_users(pl_id=None):
	from app.users.models import User

	_list = ["-"]
	try:
		if pl_id:
			records = User.query.filter_by(plant_id=pl_id, active=True).order_by(User.full_name.asc()).all()
		else:
			records = User.query.filter_by(active=True).order_by(User.full_name.asc()).all()
			
		for r in records:
			_list.append(f"{r.id} - {r.full_name}")
	except Exception as err:
		print('ERROR_LIST_USERS_ACTIONS:', err)
		pass

	db.session.close()
	return _list


def list_partners():
	from app.organizations.partners.models import Partner

	_list = ["-"]
	try:
		records = Partner.query.order_by(Partner.organization.asc()).all()
		for r in records:
			_list.append(f"{r.id} - {r.organization}")
	except Exception as err:
		print('ERROR_LIST_PARTNERS_ACTIONS:', err)
		pass

	db.session.close()
	return _list


def list_partner_sites(p_id=None):
	from app.organizations.partner_sites.models import PartnerSite

	_list = ["-"]
	try:
		if p_id:
			records = PartnerSite.query.filter_by(partner_id=p_id).order_by(PartnerSite.site.asc()).all()
		else:
			records = PartnerSite.query.order_by(PartnerSite.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.site}")
	except Exception as err:
		print('ERROR_LIST_PARTNER_SITES_ACTIONS:', err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


def list_partner_contacts(p_id=None):
	from app.organizations.partner_contacts.models import PartnerContact

	_list = ["-"]
	try:
		if p_id:
			records = PartnerContact.query.filter_by(partner_id=p_id).order_by(PartnerContact.full_name.asc()).all()
		else:
			records = PartnerContact.query.order_by(PartnerContact.id.asc()).all()

		for r in records:
			_list.append(f"{r.id} - {r.full_name}")
	except Exception as err:
		print('ERROR_LIST_PARTNER_CONTACTS_ACTIONS:', err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


def list_plant_sites(pl_id=None):
	from app.organizations.plant_sites.models import PlantSite

	_list = ["-"]
	try:
		if pl_id:
			records = PlantSite.query.filter_by(partner_id=pl_id, active=True).order_by(PlantSite.site.asc()).all()
		else:
			records = PlantSite.query.order_by(PlantSite.id.asc()).all()
			
		if records:
			for r in records:
				_list.append(f"{r.id} - {r.site}")
	except Exception as err:
		print('ERROR_LIST_PLANT_SITES_ACTIONS:', err)
		pass

	# print("LIST:", _list)
	db.session.close()
	return _list


class FormActions(FlaskForm):
	"""Form per aggiornare riga Fattura."""
	action_description = TextAreaField('Descrizione', validators=[DataRequired("Campo obbligatorio!"),
																	Length(max=500)])
	action_category = SelectField('Categoria', choices=list_opp_categories)
	
	action_date = DateField('Data', validators=[DataRequired("Campo obbligatorio!")])
	
	user_id = SelectField("Utente", validators=[DataRequired("Campo obbligatorio!")])

	action_time_spent = DecimalField('Impegno h', validators=[DataRequired("Campo obbligatorio!")], places=1)

	opp_id = IntegerField("Opportunità", validators=[DataRequired("Campo obbligatorio!")])

	plant_id = IntegerField("Azienda", validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField('Sede Operativa', validators=[Optional()])

	partner_id = SelectField("Partner", validators=[DataRequired("Campo obbligatorio!")])
	partner_site_id = SelectField("Sito Partner", validators=[Optional()])
	partner_contact_id = SelectField("Referente", validators=[Optional()])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ACTION_FORM: {self.action_description}>'

	def __str__(self):
		return f'<ACTION_FORM: {self.action_description}>'
	
	@classmethod
	def new(cls, pl_id=None, p_id=None):
		# Instantiate the form
		form = cls()
		form.action_date.data = date.today()
		form.user_id.data = f"{session['user']['id']} - {session['user']['full_name']}"
		
		# Update the choices
		form.user_id.choices = list_users(pl_id)
		form.plant_site_id.choices = list_plant_sites(pl_id)
		
		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites(p_id)
		form.partner_contact_id.choices = list_partner_contacts(p_id)
		return form

	@classmethod
	def update(cls, obj, pl_id=None, p_id=None):
		# Instantiate the form
		form = cls()

		form.action_description.data = obj.action_description
		form.action_category.data = obj.action_category
		
		form.action_date.data = obj.action_date
		
		form.action_time_spent.data = obj.action_time_spent or None

		form.opp_id.data = obj.opp_id
		
		form.plant_id.data = obj.plant_id

		form.note.data = obj.note or None
		
		# Update the choices
		form.user_id.choices = list_users(pl_id)
		form.plant_site_id.choices = list_plant_sites(pl_id)
		
		form.partner_id.choices = list_partners()
		form.partner_site_id.choices = list_partner_sites(p_id)
		form.partner_contact_id.choices = list_partner_contacts(p_id)
		return form

	def to_dict(self):
		"""Converte form in dict."""
		from app.functions import not_empty, date_to_str
		
		if self.user_id.data and self.user_id.data not in ['', '-']:
			user_id = int(self.user_id.data.split(' - ')[0])
		else:
			user_id = None
			
		if self.plant_site_id.data and self.plant_site_id.data not in ['', '-']:
			plant_site_id = int(self.plant_site_id.data.split(' - ')[0])
		else:
			plant_site_id = None

		if self.partner_site_id.data and self.partner_site_id.data not in ['', '-']:
			partner_site_id = int(self.partner_site_id.data.split(' - ')[0])
		else:
			partner_site_id = None
		
		if self.partner_contact_id.data and self.partner_contact_id.data not in ['', '-']:
			partner_contact_id = int(self.partner_contact_id.data.split(' - ')[0])
		else:
			partner_contact_id = None

		return {
			'action_description': not_empty(self.action_description.data.strip().replace('  ', ' ')),
			'action_category': self.action_category.data,

			'action_date': date_to_str(self.action_date.data),
			
			'user_id': user_id,
			
			'action_time_spent': float(self.action_time_spent.data),
			
			'opp_id': int(self.opp_id.data),

			'plant_id': int(self.plant_id.data),
			'plant_site_id': plant_site_id,

			'partner_id': int(self.partner_id.data.split(' - ')[0]),
			'partner_site_id': partner_site_id,
			'partner_contact_id': partner_contact_id,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.now()
		}
