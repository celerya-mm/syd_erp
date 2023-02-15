import json
from datetime import datetime

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from config import db

from .forms import FormPartnerCreate, FormPartnerUpdate
from .models import Partner
from ..functions import token_user_validate, access_required, status_true_false, not_empty, mount_full_address

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
	form = FormPartnerCreate()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))
		# print('NEW_PARTNER:', json.dumps(form_data, indent=2))

		if "client" not in form_data.keys() or form_data["client"] is None:
			form_data["client"] = False
		if "supplier" not in form_data.keys() or form_data["supplier"] is None:
			form_data["supplier"] = False
		if "partner" not in form_data.keys() or form_data["partner"] is None:
			form_data["partner"] = False

		new_p = Partner(
			organization=form_data["organization"].strip().replace('  ', ' '),

			client=status_true_false(form_data["client"]),
			supplier=status_true_false(form_data["supplier"]),
			partner=status_true_false(form_data["partner"]),

			email=form_data["email"].strip().replace(' ', ''),
			pec=form_data["pec"].strip().replace(' ', ''),
			phone=not_empty(form_data["phone"]),

			address=not_empty(form_data["address"]),
			cap=not_empty(form_data["cap"]),
			city=not_empty(form_data["city"]),

			vat_number=form_data["vat_number"],
			fiscal_code=form_data["fiscal_code"],
			sdi_code=not_empty(form_data["sdi_code"]),

			note=not_empty(form_data["note"])
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

	# Interrogo il DB
	partner = Partner.query.get(_id)
	_partner = partner.to_dict()

	# Estraggo la storia delle modifiche per l'utente
	history_list = partner.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_partner, view=VIEW_FOR, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, h_len=len(history_list)
	)


@partner_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['partners_admin', 'partners_write'])
def partner_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import event_create

	form = FormPartnerUpdate()
	# recupero i dati
	partner = Partner.query.get(_id)

	if form.validate_on_submit():
		new_data = FormPartnerUpdate(request.form).to_dict()

		print('NEW_DATA:', json.dumps(new_data, indent=2, default=str))

		previous_data = partner.to_dict()
		previous_data.pop("updated_at")

		partner.organization = new_data["organization"]

		partner.client = new_data["client"]
		partner.supplier = new_data["supplier"]
		partner.partner = new_data["partner"]

		partner.email = new_data["email"]
		partner.pec = new_data["pec"]
		partner.phone = new_data["phone"]

		partner.address = new_data["address"]
		partner.cap = new_data["cap"]
		partner.city = new_data["city"]
		partner.full_address = new_data["full_address"]

		partner.vat_number = new_data["vat_number"]
		partner.fiscal_code = new_data["fiscal_code"]
		partner.sdi_code = not_empty(new_data["sdi_code"])

		partner.note = new_data["note"]
		partner.updated_at = datetime.now()
		try:
			Partner.update()
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
		form.organization.data = partner.organization

		form.client.data = partner.client
		form.supplier.data = partner.supplier
		form.partner.data = partner.partner

		form.email.data = partner.email
		form.pec.data = partner.pec
		form.phone.data = partner.phone

		form.address.data = partner.address
		form.cap.data = partner.cap
		form.city.data = partner.city

		form.vat_number.data = partner.vat_number
		form.fiscal_code.data = partner.fiscal_code
		form.sdi_code.data = partner.sdi_code

		form.note.data = partner.note

		_info = {
			'created_at': partner.created_at,
			'updated_at': partner.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
