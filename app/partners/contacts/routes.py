import json

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from config import db

from .forms import FormContactCreate, FormContactUpdate
from .models import Contact
from app.functions import token_user_validate, access_required, not_empty

contact_bp = Blueprint(
	'contact_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "contact_bp.contact_view"
VIEW_HTML = "contact_view.html"

CREATE = "/create/"
CREATE_FOR = "contact_bp.contact_create"
CREATE_HTML = "contact_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "contact_bp.contact_view_detail"
DETAIL_HTML = "contact_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "contact_bp.contact_update"
UPDATE_HTML = "contact_update.html"


@contact_bp.route(VIEW, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['contacts_admin', 'contacts_read'])
def contact_view():
	"""Visualizzo informazioni Contacts."""
	from app.partners.oraganizations.routes import DETAIL_FOR as PARTNER_DETAIL

	# Estraggo la lista dei partners
	_list = Contact.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL)


@contact_bp.route(CREATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['contacts_admin', 'contacts_write'])
def contact_create():
	"""Creazione Contact."""
	form = FormContactCreate()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))
		# print('NEW_CONTACT:', json.dumps(form_data, indent=2))

		new_p = Contact(
			name=form_data['form_data'],
			last_name=form_data['last_name'],

			role=form_data['role'],
			partner_id=form_data['partner_id'],

			email=form_data["email"],
			phone=not_empty(form_data["phone"]),

			note=not_empty(form_data["note"])
		)
		try:
			Contact.create(new_p)
			flash("CONTACT creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@contact_bp.route(DETAIL, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['contacts_admin', 'contacts_read'])
def contact_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.partners.oraganizations.routes import DETAIL_FOR as PARTNER_DETAIL

	# Interrogo il DB
	contact = Contact.query.get(_id)
	_contact = contact.to_dict()

	# Estraggo la storia delle modifiche per l'utente
	history_list = contact.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_contact, view=VIEW_FOR, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, h_len=len(history_list), partner_detail=PARTNER_DETAIL
	)


@contact_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['contacts_admin', 'contacts_write'])
def contact_update(_id):
	"""Aggiorna dati Contact."""
	from app.event_db.routes import event_create

	# recupero i dati
	contact = Contact.query.get(_id)
	form = FormContactUpdate(obj=contact)

	if request.method == 'POST' and form.validate():
		new_data = FormContactUpdate(request.form).to_dict()

		previous_data = contact.to_dict()
		previous_data.pop("updated_at")

		try:
			Contact.update(_id, new_data)
			flash("PARTNER aggiornato correttamente.")
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
			"table": Contact.__tablename__,
			"Modification": f"Update PARTNER whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, partner_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		_info = {
			'created_at': contact.created_at,
			'updated_at': contact.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
