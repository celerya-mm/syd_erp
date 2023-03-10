import json  # noqa

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, timer_func
from app.organizations.partner_sites.models import PartnerSite
from app.organizations.partners.models import Partner
from .forms import FormPartnerContact
from .models import PartnerContact

partner_contact_bp = Blueprint(
	'partner_contact_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = PartnerContact.__tablename__
BLUE_PRINT, B_PRINT = partner_contact_bp, 'partner_contact_bp'

VIEW = "/view/"
VIEW_FOR = f"{B_PRINT}.{TABLE}_view"
VIEW_HTML = f"{TABLE}_view.html"

CREATE = "/create/<int:p_id>/<int:s_id>/"
CREATE_FOR = f"{B_PRINT}.{TABLE}_create"
CREATE_HTML = f"{TABLE}_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = f"{B_PRINT}.{TABLE}_view_detail"
DETAIL_HTML = f"{TABLE}_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = f"{B_PRINT}.{TABLE}_update"
UPDATE_HTML = f"{TABLE}_update.html"


@BLUE_PRINT.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def partner_contacts_view():
	"""Visualizzo informazioni Contacts."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	
	# Estraggo la lista dei partners
	_list = PartnerContact.query.all()
	_list = [r.to_dict() for r in _list]
	
	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL)


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def partner_contacts_create(p_id, s_id=None):
	"""Creazione Contact."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL
	
	form = FormPartnerContact.new(p_id=p_id)
	if request.method == 'POST' and form.validate():
		try:
			form_data = FormPartnerContact(request.form).to_dict()
			# print('NEW_CONTACT:', json.dumps(form_data, indent=2))
			
			new_p = PartnerContact(
				name=form_data['name'],
				last_name=form_data['last_name'],
				full_name=form_data['full_name'],
				
				role=form_data['role'],
				
				email=form_data["email"],
				phone=form_data["phone"],
				
				partner_id=form_data['partner_id'],
				partner_site_id=form_data['partner_site_id'],
				
				note=form_data["note"],
				created_at=form_data["updated_at"],
				updated_at=form_data["updated_at"]
			)
			
			PartnerContact.create(new_p)
			flash("CONTACT creato correttamente.")
			
			if s_id not in [None, 0]:
				return redirect(url_for(SITE_DETAIL, _id=s_id))
			else:
				return redirect(url_for(PARTNER_DETAIL, _id=p_id))
		
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, partner_view=PARTNER_DETAIL, p_id=p_id,
			                       site_view=SITE_DETAIL, s_id=s_id)
	else:
		partner = Partner.query.get(p_id)
		form.partner_id.data = f'{partner.id} - {partner.organization}'
		# print('PARTNER:', form.partner_id.data)
		
		if s_id not in [None, 0]:
			site = PartnerSite.query.get(s_id)
			form.partner_site_id.data = f'{site.id} - {site.site}'
		# print('SITE:', form.partner_site_id.data)
		
		db.session.close()
		return render_template(CREATE_HTML, form=form, partner_view=PARTNER_DETAIL, p_id=p_id,
		                       site_view=SITE_DETAIL, s_id=s_id)


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def partner_contacts_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL
	
	# Interrogo il DB
	contact = PartnerContact.query \
		.options(joinedload(PartnerContact.partner)) \
		.options(joinedload(PartnerContact.partner_site)).get(_id)
	_contact = contact.to_dict()
	
	# Estraggo la storia delle modifiche per l'utente
	history_list = contact.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []
	
	_contact["partner_id"] = f'{contact.partner.id} - {contact.partner.organization}'
	p_id = contact.partner.id
	
	_contact["site_id"] = f'{contact.partner_site.id} - {contact.partner_site.site}' if contact.partner_site else None
	s_id = contact.partner_site.id if contact.partner_site else None
	
	db.session.close()
	return render_template(
		DETAIL_HTML, form=_contact, view=VIEW_FOR, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, h_len=len(history_list), partner_detail=PARTNER_DETAIL, p_id=p_id,
		site_detail=SITE_DETAIL, s_id=s_id
	)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def partner_contacts_update(_id):
	"""Aggiorna dati Contact."""
	from app.event_db.routes import events_db_create
	
	# recupero i dati
	contact = PartnerContact.query \
		.options(joinedload(PartnerContact.partner)) \
		.options(joinedload(PartnerContact.partner_site)) \
		.get(_id)
	
	session['partner_id'] = contact.partner_id
	form = FormPartnerContact.update(obj=contact, p_id=contact.partner_id)
	
	if request.method == 'POST' and form.validate():
		new_data = FormPartnerContact(request.form).to_dict()
		
		previous_data = contact.to_dict()
		previous_data.pop("updated_at")
		
		try:
			PartnerContact.update(_id, new_data)
			session.pop('partner_id')
			flash("CONTATTO PARTNER aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': contact.created_at,
				'updated_at': contact.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
		
		_event = {
			"username": session["user"]["username"],
			"table": PartnerContact.__tablename__,
			"Modification": f"Update PARTNER CONTACT whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, partner_contact_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		form.partner_id.data = f'{contact.partner.id} - {contact.partner.organization}'
		form.partner_site_id.data = f'{contact.partner_site.id} - {contact.partner_site.site}' \
			if contact.partner_site else None
		
		_info = {
			'created_at': contact.created_at,
			'updated_at': contact.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
