import json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.functions import token_user_validate, access_required, timer_func
from app.app import session, db
from .forms import FormPartnerSite
from .models import PartnerSite

partner_site_bp = Blueprint(
	'partner_site_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "partner_site_bp.partner_site_view"
VIEW_HTML = "partner_site_view.html"

CREATE = "/create/<int:p_id>/"
CREATE_FOR = "partner_site_bp.partner_site_create"
CREATE_HTML = "partner_site_create.html"

DETAIL = "/view/detail/<int:_id>/"
DETAIL_FOR = "partner_site_bp.partner_site_view_detail"
DETAIL_HTML = "partner_site_view_detail.html"

UPDATE = "/update/<int:_id>/"
UPDATE_FOR = "partner_site_bp.partner_site_update"
UPDATE_HTML = "partner_site_update.html"


@partner_site_bp.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['partner_sites_admin', 'partner_sites_read'])
def partner_site_view():
	"""Visualizzo informazioni Sito."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL_FOR

	# Estraggo la lista dei partners
	_list = PartnerSite.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR,
						   partner_detail=PARTNER_DETAIL_FOR)


@partner_site_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['partner_sites_admin', 'partner_sites_write'])
def partner_site_create(p_id):
	"""Creazione Sito."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL_FOR

	form = FormPartnerSite()
	if form.validate_on_submit():
		form_data = FormPartnerSite(request.form).to_dict()
		# print('TYPE:', type(form_data), 'NEW_PARTNER:', json.dumps(form_data, indent=2))

		new_p = PartnerSite(
			site=form_data["site"],

			active=form_data["active"],
			site_type=form_data["site_type"],

			client=form_data["client"],
			supplier=form_data["supplier"],
			partner=form_data["partner"],

			email=form_data["email"],
			pec=form_data["pec"],
			phone=form_data["phone"],

			address=form_data["address"],
			cap=form_data["cap"],
			city=form_data["city"],
			full_address=form_data["full_address"],

			vat_number=form_data["vat_number"],
			fiscal_code=form_data["fiscal_code"],
			sdi_code=form_data["sdi_code"],

			partner_id=form_data["partner_id"],

			note=form_data["note"],

			created_at=form_data["updated_at"],
			updated_at=form_data["updated_at"]
		)
		try:
			PartnerSite.create(new_p)
			flash("SITO creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		from ..partners.models import Partner
		partner = Partner.query.get(p_id)
		form.partner_id.data = f'{partner.id} - {partner.organization}'
		db.session.close()
		partner = f'[ {partner.id} ] - {partner.organization}'
		# print("PARTNER:", form.partner_id.data)
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR, p_id=p_id, partner_detail=PARTNER_DETAIL_FOR,
							   partner=partner)


@partner_site_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['partner_sites_admin', 'partner_sites_read'])
def partner_site_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_contacts.routes import DETAIL_FOR as CONTACT_DETAIL, CREATE_FOR as CONTACT_CREATE_FOR
	from app.orders.items.routes import DETAIL_FOR as ITEM_DETAIL, CREATE_FOR as ITEM_CREATE_FOR

	# Interrogo il DB
	site = PartnerSite.query.options(joinedload(PartnerSite.back_partner)).get(_id)
	_site = site.to_dict()

	p_id = _site['partner_id']
	_site['partner_id'] = f'{site.back_partner.id} - {site.back_partner.organization}'
	# print('PARTNER_SITE:', json.dumps(_site, indent=2))

	# Estraggo la storia delle modifiche per il record
	history_list = site.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Estraggo la lista dei contatti
	contacts_list = site.contacts
	if contacts_list:
		contacts_list = [contact.to_dict() for contact in contacts_list]
	else:
		contacts_list = []

	# Estraggo la lista degli articoli
	items_list = site.items
	if items_list:
		items_list = [item.to_dict() for item in items_list]
	else:
		items_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_site, view=VIEW_FOR, update=UPDATE_FOR, partner_detail=PARTNER_DETAIL, p_id=p_id,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		contact_detail=CONTACT_DETAIL, contacts_list=contacts_list, c_len=len(contacts_list),
		contact_create=CONTACT_CREATE_FOR,
		item_create=ITEM_CREATE_FOR, item_detail=ITEM_DETAIL, items_list=items_list, i_len=len(items_list)
	)


@partner_site_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['partner_sites_admin', 'partner_sites_write'])
def partner_site_update(_id):
	"""Aggiorna dati Sito."""
	from app.event_db.routes import event_create

	# recupero i dati
	site = PartnerSite.query.options(joinedload(PartnerSite.back_partner)).get(_id)
	session['partner_site_id'] = _id
	form = FormPartnerSite.update(obj=site)

	if request.method == 'POST' and form.validate():
		new_data = FormPartnerSite(request.form).to_dict()

		previous_data = site.to_dict()
		previous_data.pop("updated_at")

		try:
			PartnerSite.update(_id, new_data)
			session.pop('partner_site_id')
			flash("SITO - PARTNER aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': site.created_at,
				'updated_at': site.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": PartnerSite.__tablename__,
			"Modification": f"Update PARTNER whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, partner_site_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		form.partner_id.data = f'{site.back_partner.id} - {site.back_partner.organization}'
		_info = {
			'created_at': site.created_at,
			'updated_at': site.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)
