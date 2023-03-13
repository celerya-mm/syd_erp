import json  # noqa
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, serialize_dict, timer_func  # noqa
from .forms import FormActions
from .models import Action

action_bp = Blueprint(
	'action_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = Action.__tablename__
BLUE_PRINT, B_PRINT = action_bp, 'action_bp'

CREATE = "/create/<int:opp_id>/<int:pl_id>/<int:pls_id>/<int:p_id>/<int:ps_id>/<int:pc_id>/"
CREATE_FOR = f"{B_PRINT}.{TABLE}_create"
CREATE_HTML = f"{TABLE}_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = f"{B_PRINT}.{TABLE}_view_detail"
DETAIL_HTML = f"{TABLE}_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = f"{B_PRINT}.{TABLE}_update"
UPDATE_HTML = f"{TABLE}_update.html"

DELETE = "/delete/<int:_id>/<int:op_id>/"
DELETE_FOR = f"{B_PRINT}.{TABLE}_delete"


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def actions_create(opp_id, pl_id, pls_id, p_id, ps_id, pc_id):
	"""Creazione Azione."""
	from app.business.opportunities.routes import DETAIL_FOR as OPP_DETAIL
	
	from app.organizations.plant_sites.models import PlantSite
	
	from app.organizations.partners.models import Partner
	from app.organizations.partner_sites.models import PartnerSite
	from app.organizations.partner_contacts.models import PartnerContact

	form = FormActions.new(pl_id=pl_id, p_id=p_id)
	if request.method == 'POST' and form.validate():
		try:
			form_data = FormActions(request.form).to_dict()
			# print('NEW_ACTIONS:', json.dumps(form_data, indent=2))

			_time = datetime.now()

			new_action = Action(
				action_description=form_data['action_description'],
				action_category=form_data['action_category'],
				
				action_date=form_data['action_date'],

				user_id=form_data['user_id'],
				
				action_time_spent=form_data['action_time_spent'],
				
				opp_id=opp_id,
				
				plant_id=pl_id,
				plant_site_id=form_data['plant_site_id'],
				
				partner_id=form_data['partner_id'],
				partner_site_id=form_data['partner_site_id'],
				partner_contact_id=form_data['partner_contact_id'],

				note=None,
				created_at=_time,
				updated_at=_time
			)

			Action.create(new_action)
			flash("ACTION creata correttamente.")

			return redirect(url_for(OPP_DETAIL, _id=opp_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, opp_view=OPP_DETAIL, op_id=opp_id)
	else:
		form.opp_id.data = opp_id
		form.plant_id.data = pl_id
		
		plant_site = PlantSite.query.get(pls_id)
		form.plant_site_id.data = f'{plant_site.id} - {plant_site.site}' if plant_site else '-'
		
		partner = Partner.query.get(p_id)
		form.partner_id.data = f'{partner.id} - {partner.organization}'
		
		p_site = PartnerSite.query.get(ps_id)
		form.partner_site_id.data = f'{p_site.id} - {p_site.site}' if p_site else '-'
		
		p_contact = PartnerContact.query.get(pc_id)
		form.partner_contact_id.data = f'{p_contact.id} - {p_contact.full_name}' if p_contact else '-'
		
		return render_template(CREATE_HTML, form=form, opp_view=OPP_DETAIL, op_id=opp_id)


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def actions_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	
	from app.users.routes import DETAIL_FOR as USER_DETAIL
	
	from app.organizations.plants.routes import DETAIL_FOR as PLANT_DETAIL
	from app.organizations.plant_sites.routes import DETAIL_FOR as PLANT_SITE_DETAIL
	
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL
	from app.organizations.partner_contacts.routes import DETAIL_FOR as CONTACT_DETAIL
	
	from app.business.opportunities.routes import DETAIL_FOR as OPP_DETAIL

	# Interrogo il DB
	action = Action.query \
		.options(joinedload(Action.user)) \
		.options(joinedload(Action.plant)) \
		.options(joinedload(Action.plant_site)) \
		.options(joinedload(Action.partner)) \
		.options(joinedload(Action.partner_site)) \
		.options(joinedload(Action.partner_contact)) \
		.get(_id)

	_action = action.to_dict()
	
	# Estraggo l'Utente
	_action['user_id'] = f'{action.user.id} - {action.user.full_name}'
	u_id = action.user.id
	
	# Estraggo la sede principale
	_action['plant_id'] = f'{action.plant.id} - {action.plant.organization}'
	pl_id = action.plant.id
	
	# Estraggo la sede secondaria
	_action['plant_site_id'] = f'{action.plant_site.id} - {action.plant_site.site}' if action.plant_site else None
	pls_id = action.plant_site.id if action.plant_site else 0
	
	# Estraggo il Partner
	_action['partner_id'] = f'{action.partner.id} - {action.partner.organization}'
	p_id = action.partner.id
	
	# Estraggo la sede secondaria del Partner
	_action['partner_site_id'] = f'{action.partner_site.id} - {action.partner_site.site}' if action.partner_site else None  # noqa
	ps_id = action.partner_site.id if action.partner_site else 0
	
	# Estraggo i dati del referente
	_action['partner_contact_id'] = f'{action.partner_contact.id} - {action.partner_contact.full_name}'
	pc_id = action.partner_contact.id
	
	# Estraggo la storia delle modifiche per il record
	history_list = [event.to_dict() for event in action.events] if action.events else []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_action, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list,              h_len=len(history_list),
		plant_detail=PLANT_DETAIL,              pl_id=pl_id,
		plant_site_detail=PLANT_SITE_DETAIL,    pls_id=pls_id,
		user_detail=USER_DETAIL,                u_id=u_id,
		p_detail=PARTNER_DETAIL,                p_id=p_id,
		p_site_detail=SITE_DETAIL,              ps_id=ps_id,
		p_contact_detail=CONTACT_DETAIL,        pc_id=pc_id,
		opp_detail=OPP_DETAIL
	)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def actions_update(_id):
	"""Aggiorna dati Riga Fattura."""
	from app.event_db.routes import events_db_create

	# recupero i dati
	action = Action.query \
		.options(joinedload(Action.user)) \
		.options(joinedload(Action.plant)) \
		.options(joinedload(Action.plant_site)) \
		.options(joinedload(Action.partner)) \
		.options(joinedload(Action.partner_site)) \
		.options(joinedload(Action.partner_contact)) \
		.get(_id)

	form = FormActions.update(obj=action, pl_id=action.plant_id, p_id=action.partner_id)

	if request.method == 'POST' and form.validate():
		new_data = FormActions(request.form).to_dict()

		previous_data = action.to_dict()
		previous_data.pop("updated_at")
		previous_data['action_time_spent'] = str(previous_data['action_time_spent'])

		try:
			Action.update(_id, new_data)
			flash("ACTION aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': action.created_at,
				'updated_at': action.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR,
			                       op_id=form.opp_id.data)

		_event = {
			"username": session["user"]["username"],
			"table": Action.__tablename__,
			"Modification": f"Update ACTION whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, action_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		# Estraggo l'Utente
		form.user_id.data = f'{action.user.id} - {action.user.full_name}'
		
		# Estraggo la sede secondaria
		form.plant_site_id.data = f'{action.plant_site.id} - {action.plant_site.site}' if action.plant_site else None
		
		# Estraggo il Partner
		form.partner_id.data = f'{action.partner.id} - {action.partner.organization}'
		
		# Estraggo la sede secondaria del Partner
		form.partner_site_id.data = f'{action.partner_site.id} - {action.partner_site.site}' if action.partner_site else None  # noqa
		
		# Estraggo i dati del referente
		form.partner_contact_id.data = f'{action.partner_contact.id} - {action.partner_contact.full_name}' if action.partner_contact else None  # noqa

		_info = {
			'created_at': action.created_at,
			'updated_at': action.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR, op_id=form.opp_id.data)


@BLUE_PRINT.route(DELETE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def actions_delete(_id, op_id):
	"""Cancella Azione"""
	from app.business.opportunities.routes import DETAIL_FOR as OPP_DETAIL
	try:
		Action.remove(_id)
		flash(f'ACTION id [{_id}] OPPORTUNITY id [{op_id}] rimossa correttamente.')
		return redirect(url_for(OPP_DETAIL, _id=op_id))
	except Exception as err:
		flash(f'ACTION id [{_id}] OPPORTUNITY id [{op_id}] NON rimossa: {err}.')
		return redirect(url_for(OPP_DETAIL, _id=op_id))
