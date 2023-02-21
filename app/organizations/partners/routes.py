from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from app.app import session, db
from app.functions import token_user_validate, access_required
from .forms import FormPartner
from .models import Partner

partner_bp = Blueprint(
	'partner_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "partner_bp.partner_view"
VIEW_HTML = "partner_view.html"

CREATE = "/create/"
CREATE_FOR = "partner_bp.partner_create"
CREATE_HTML = "partner_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "partner_bp.partner_view_detail"
DETAIL_HTML = "partner_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "partner_bp.partner_update"
UPDATE_HTML = "partner_update.html"


@partner_bp.route(VIEW, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['partners_admin', 'partners_read'])
def partner_view():
	"""Visualizzo informazioni Partner."""
	# Estraggo la lista dei partners
	_list = Partner.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR)


@partner_bp.route(CREATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['partners_admin', 'partners_write'])
def partner_create():
	"""Creazione Partner."""
	form = FormPartner()
	if form.validate_on_submit():
		form_data = FormPartner(request.form).to_dict()
		# print('TYPE:', type(form_data), 'NEW_PARTNER:', json.dumps(form_data, indent=2))y

		new_p = Partner(
			organization=form_data["organization"].strip().replace('  ', ' '),

			active=True,
			site_type=form_data["site_type"],

			client=form_data["client"],
			supplier=form_data["supplier"],
			partner=form_data["partner"],

			email=form_data["email"].strip().replace(' ', ''),
			pec=form_data["pec"].strip().replace(' ', ''),
			phone=form_data["phone"],

			address=form_data["address"],
			cap=form_data["cap"],
			city=form_data["city"],

			vat_number=form_data["vat_number"],
			fiscal_code=form_data["fiscal_code"],
			sdi_code=form_data["sdi_code"],

			payment_condition=form_data["payment_condition"],
			iban=form_data["iban"],
			swift=form_data["swift"],

			note=form_data["note"]
		)
		try:
			Partner.create(new_p)
			flash("PARTNER creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@partner_bp.route(DETAIL, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['partners_admin', 'partners_read'])
def partner_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partner_contacts.routes import DETAIL_FOR as CONTACT_DETAIL, CREATE_FOR as CONTACT_CREATE_FOR
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL, CREATE_FOR as SITE_CREATE_FOR
	from app.orders.items.routes import DETAIL_FOR as ITEM_DETAIL, CREATE_FOR as ITEM_CREATE_FOR

	# Interrogo il DB
	partner = Partner.query.get(_id)
	_partner = partner.to_dict()

	# Estraggo la storia delle modifiche per il record
	history_list = partner.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Estraggo la lista dei contatti
	contacts_list = partner.contacts
	if contacts_list:
		contacts_list = [contact.to_dict() for contact in contacts_list]
	else:
		contacts_list = []

	# Estraggo la lista dei siti
	sites_list = partner.sites
	if sites_list:
		sites_list = [site.to_dict() for site in sites_list]
	else:
		sites_list = []

	# Estraggo la lista degli articoli
	items_list = partner.items
	if items_list:
		items_list = [item.to_dict() for item in items_list]
	else:
		items_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_partner, view=VIEW_FOR, update=UPDATE_FOR,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		contact_detail=CONTACT_DETAIL, contacts_list=contacts_list, c_len=len(contacts_list),
		contact_create=CONTACT_CREATE_FOR,
		site_create=SITE_CREATE_FOR, site_detail=SITE_DETAIL, sites_list=sites_list, s_len=len(sites_list),
		item_create=ITEM_CREATE_FOR, item_detail=ITEM_DETAIL, items_list=items_list, i_len=len(items_list)
	)


@partner_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['partners_admin', 'partners_write'])
def partner_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import event_create

	# recupero i dati
	partner = Partner.query.get(_id)
	form = FormPartner(obj=partner)

	if request.method == 'POST' and form.validate():
		new_data = FormPartner(request.form).to_dict()

		previous_data = partner.to_dict()
		previous_data.pop("updated_at")

		try:
			Partner.update(_id, new_data)
			session.pop('partner_id')
			flash("PARTNER aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': partner.created_at,
				'updated_at': partner.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Partner.__tablename__,
			"Modification": f"Update PARTNER whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, partner_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		session['partner_id'] = _id
		_info = {
			'created_at': partner.created_at,
			'updated_at': partner.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
