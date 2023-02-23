from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, timer_func
from .forms import FormPlantSite
from .models import PlantSite

plant_site_bp = Blueprint(
	'plant_site_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "plant_site_bp.plant_site_view"
VIEW_HTML = "plant_site_view.html"

CREATE = "/create/<int:p_id>/"
CREATE_FOR = "plant_site_bp.plant_site_create"
CREATE_HTML = "plant_site_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "plant_site_bp.plant_site_view_detail"
DETAIL_HTML = "plant_site_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "plant_site_bp.plant_site_update"
UPDATE_HTML = "plant_site_update.html"


@plant_site_bp.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['plant_sites_admin', 'plant_sites_read'])
def plant_site_view():
	"""Visualizzo informazioni Partner."""
	# Estraggo la lista dei partners
	_list = PlantSite.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR)


@plant_site_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['plant_sites_admin', 'plant_sites_write'])
def plant_site_create(p_id):
	"""Creazione Partner."""
	from app.organizations.plant.models import Plant

	form = FormPlantSite.new()
	if form.validate_on_submit():
		form_data = FormPlantSite(request.form).to_dict()
		# print('TYPE:', type(form_data), 'NEW_PARTNER:', json.dumps(form_data, indent=2))

		new_p = PlantSite(
			organization=form_data["organization"],

			active=form_data["active"],
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

			plant_id=form_data["plant_id"],

			note=form_data["note"],
			created_at=form_data["updated_at"],
			updated_at=form_data["updated_at"]
		)
		try:
			PlantSite.create(new_p)
			flash("SITO creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		plant = Plant.query.get(p_id)
		form.organization.data = plant.organization
		form.active.data = True
		form.email.data = plant.email
		form.pec.data = plant.pec
		form.phone.data = plant.phone
		form.vat_number.data = plant.vat_number
		form.fiscal_code.data = plant.fiscal_code
		form.sdi_code.data = plant.sdi_code
		form.plant_id.data = f'{plant.id} - {plant.organization}'
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@plant_site_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['plant_sites_admin', 'plant_sites_read'])
def plant_site_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.plant.routes import DETAIL_FOR as PLANT_DETAIL

	# Interrogo il DB
	partner = PlantSite.query.options(joinedload(PlantSite.back_plant)).get(_id)
	_partner = partner.to_dict()

	p_id = _partner['plant_id']
	_partner['plant_id'] = f'{partner.back_plant.id} - {partner.back_plant.organization}'

	# Estraggo la storia delle modifiche per il record
	history_list = partner.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_partner, view=VIEW_FOR, update=UPDATE_FOR,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		plant_detail=PLANT_DETAIL, p_id=p_id,
	)


@plant_site_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['plant_sites_admin', 'plant_sites_write'])
def plant_site_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import event_create

	# recupero i dati
	plant_site = PlantSite.query.options(joinedload(PlantSite.back_plant)).get(_id)
	form = FormPlantSite.update(obj=plant_site)

	if request.method == 'POST' and form.validate():
		new_data = FormPlantSite(request.form).to_dict()

		previous_data = plant_site.to_dict()
		previous_data.pop("updated_at")

		try:
			PlantSite.update(_id, new_data)
			session.pop('plant_site_id')
			flash("SITO aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': plant_site.created_at,
				'updated_at': plant_site.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": PlantSite.__tablename__,
			"Modification": f"Update SITO whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, plant_site_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		form.plant_id.data = f'{plant_site.back_plant.id} - {plant_site.back_plant.organization}'
		session['plant_site_id'] = _id

		_info = {
			'created_at': plant_site.created_at,
			'updated_at': plant_site.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
