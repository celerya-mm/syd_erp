from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from app.app import session, db
from app.functions import token_user_validate, access_required, timer_func
from .forms import FormPlant
from .models import Plant

plant_bp = Blueprint(
	'plant_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = Plant.__tablename__
BLUE_PRINT, B_PRINT = plant_bp, 'plant_bp'

VIEW = "/view/"
VIEW_FOR = f"{B_PRINT}.{TABLE}_view"
VIEW_HTML = f"{TABLE}_view.html"

CREATE = "/create/"
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
def plants_view():
	"""Visualizzo informazioni Partner."""
	# Estraggo la lista dei partners
	_list = Plant.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR)


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def plants_create():
	"""Creazione Partner."""
	form = FormPlant()
	if form.validate_on_submit():
		form_data = FormPlant(request.form).to_dict()
		# print('TYPE:', type(form_data), 'NEW_PARTNER:', json.dumps(form_data, indent=2))

		new_p = Plant(
			organization=form_data["organization"],

			active=True,
			site_type=form_data["site_type"],

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

			note=form_data["note"],
			created_at=form_data["updated_at"],
			updated_at=form_data["updated_at"]
		)
		try:
			Plant.create(new_p)
			flash("PARTNER creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def plants_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.plant_sites.routes import CREATE_FOR as SITE_CREATE, DETAIL_FOR as SITE_DETAIL

	# Interrogo il DB
	partner = Plant.query.get(_id)
	_partner = partner.to_dict()

	# Estraggo la storia delle modifiche per il record
	history_list = partner.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Estraggo la lista dei siti collegati
	sites_list = partner.plant_site
	if sites_list:
		sites_list = [site.to_dict() for site in sites_list]
	else:
		sites_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_partner, view=VIEW_FOR, update=UPDATE_FOR, id=_id,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		site_create=SITE_CREATE, site_detail=SITE_DETAIL, sites_list=sites_list, s_len=len(sites_list)
	)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def plants_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import events_db_create

	# recupero i dati
	partner = Plant.query.get(_id)
	session['plant_id'] = _id
	form = FormPlant(obj=partner)

	if request.method == 'POST' and form.validate():
		new_data = FormPlant(request.form).to_dict()

		previous_data = partner.to_dict()
		previous_data.pop("updated_at")

		try:
			Plant.update(_id, new_data)
			session.pop('plant_id')
			flash("SEDE aggiornata correttamente.")
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
			"table": Plant.__tablename__,
			"Modification": f"Update SEDE whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, plant_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		_info = {
			'created_at': partner.created_at,
			'updated_at': partner.updated_at,
		}

		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
