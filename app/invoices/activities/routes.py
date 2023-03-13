import json  # noqa
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, not_empty, timer_func
from .forms import FormActivity
from .models import Activity
from app.organizations.plant_sites.models import PlantSite

activity_bp = Blueprint(
	'activity_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = Activity.__tablename__
BLUE_PRINT, B_PRINT = activity_bp, 'activity_bp'

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
def activities_view():
	"""Visualizzo informazioni Activities."""
	from app.organizations.plant_sites.routes import DETAIL_FOR as SITE_DETAIL

	# Estraggo la lista dei partners
	_list = Activity.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, p_id=1, s_id=0,
						   detail=DETAIL_FOR, site_detail=SITE_DETAIL)


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def activities_create(p_id, s_id=None):
	"""Creazione Activity."""
	from app.organizations.plant_sites.routes import DETAIL_FOR as SITE_DETAIL

	form = FormActivity.new(p_id=p_id)
	if request.method == 'POST' and form.validate():
		try:
			form_data = FormActivity(request.form).to_dict_new()
			# print('NEW_ITEM:', json.dumps(form_data, indent=2))

			_time = datetime.now()

			site_id = form_data["plant_site_id"].split(' - ')[0] if form_data["plant_site_id"] else None

			new_p = Activity(
				activity_code=form_data['activity_code'],

				activity_description=form_data['activity_description'],
				activity_category=form_data['activity_category'],

				activity_price=form_data['activity_price'],
				activity_currency=form_data['activity_currency'],

				activity_quantity=not_empty(form_data["activity_quantity"]),
				activity_quantity_um=not_empty(form_data["activity_quantity_um"]),

				plant_id=1,
				plant_site_id=site_id,

				note=not_empty(form_data["note"]),
				created_at=_time,
				updated_at=_time
			)
			Activity.create(new_p)
			flash("ACTIVITY creata correttamente.")

			return redirect(url_for(VIEW_FOR))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, site_view=SITE_DETAIL, s_id=s_id)
	else:
		# setto il nuovo codice_articolo
		last_id = Activity.query.order_by(Activity.id.desc()).first()
		if last_id is None:
			form.activity_code.data = 'act_0001'
		else:
			form.activity_code.data = f'act_{str(int(last_id.id) + 1).zfill(4)}'

		if s_id not in [None, 0]:
			site = PlantSite.query.get(s_id)
			form.plant_site_id.data = f'{site.id} - {site.organization}'
			# print('SITE:', form.partner_site_id.data)

		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def activities_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.plant_sites.routes import DETAIL_FOR as SITE_DETAIL

	# Interrogo il DB
	activity = Activity.query \
		.options(joinedload(Activity.plant)) \
		.options(joinedload(Activity.plant_site)).get(_id)
	_activity = activity.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = activity.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	_activity["plant_id"] = f'{activity.plant.id} - {activity.plant.organization}'
	p_id = activity.plant.id  # noqa

	if activity.plant_site:
		_activity["plant_site_id"] = f'{activity.plant_site.id} - {activity.plant_site.organization}'
		s_id = activity.plant_site.id
	else:
		s_id = 0

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_activity, view=VIEW_FOR, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, h_len=len(history_list), site_detail=SITE_DETAIL, s_id=s_id
	)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def activities_update(_id):
	"""Aggiorna dati Activity."""
	from app.event_db.routes import events_db_create

	# recupero i dati
	activity = Activity.query \
		.options(joinedload(Activity.plant)) \
		.options(joinedload(Activity.plant_site)).get(_id)

	form = FormActivity.update(obj=activity, p_id=activity.plant_id)

	if request.method == 'POST' and form.validate():
		new_data = FormActivity(request.form).to_dict()

		previous_data = activity.to_dict()
		previous_data.pop("updated_at")
		previous_data['activity_price'] = str(previous_data['activity_price'])

		try:
			Activity.update(_id, new_data)
			flash("ATTIVITA' aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': activity.created_at,
				'updated_at': activity.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Activity.__tablename__,
			"Modification": f"Update ACTIVITY whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, activity_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		# form.plant_id.data = f'{activity.plant.id} - {activity.plant.organization}'
		if activity.plant_site:
			form.plant_site_id.data = f'{activity.plant_site.id} - {activity.plant_site.organization}'

		_info = {
			'created_at': activity.created_at,
			'updated_at': activity.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)
