import json
from datetime import datetime

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from config import db

from .forms import FormPartnerCreate, FormPartnerUpdate
from .models import Partner
from app.functions import token_user_validate, access_required, status_true_false, not_empty, mount_full_address

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

	# recupero i dati
	partner = Partner.query.get(_id)
	form = FormPartnerUpdate(obj=partner)

	if request.method == 'POST' and form.validate():
		new_data = FormPartnerUpdate(request.form).to_dict()

		previous_data = partner.to_dict()
		previous_data.pop("updated_at")

		try:
			Partner.update(_id, new_data)
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
		_info = {
			'created_at': partner.created_at,
			'updated_at': partner.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
