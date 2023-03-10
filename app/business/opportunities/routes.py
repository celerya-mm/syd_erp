# import json
from datetime import datetime

import simplejson as json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, timer_func
from .forms import FormOpportunity
from .functions import dict_group_by
from .models import Opportunity

opportunity_bp = Blueprint(
	'opportunity_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "opportunity_bp.opportunity_view"
VIEW_HTML = "opportunity_view.html"

CREATE = "/create/<int:p_id>/<int:s_id>/"
CREATE_FOR = "opportunity_bp.opportunity_create"
CREATE_HTML = "opportunity_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "opportunity_bp.opportunity_view_detail"
DETAIL_HTML = "opportunity_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "opportunity_bp.opportunity_update"
UPDATE_HTML = "opportunity_update.html"


@opportunity_bp.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['opportunities_admin', 'opportunities_read'])
def opportunity_view():
	"""Visualizzo informazioni Opportunità."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	if request.method == 'POST':
		year = request.form.get('year')
		print('YEAR:', year)
		if year:
			_list = Opportunity.query.filter_by(opp_year=year).all()
			if len(_list):
				flash(f"Opportunità trovate: {len(_list)}")
			else:
				_list = Opportunity.query.all()
				flash("Nessuna Attività nel periodo cercato.")
				flash('Mostro tutti i records.')
		else:
			_list = Opportunity.query.all()
			flash(f"Nessun Anno selezionato, mostro tutti i records: {len(_list)}")
	else:
		_list = Opportunity.query.all()

	# Estraggo la lista delle opportunità
	_list = [r.to_dict() for r in _list]

	if _list:
		# raggruppo per anno ordine (5 anni max)
		g_year = dict_group_by(_list, 'opp_date', amount='opp_amount', year=True)
		y_labels = [sub['opp_date'] for sub in g_year]
		y_values = [sub['opp_amount'] for sub in g_year]

		# raggruppa per fornitore
		g_supplier = dict_group_by(_list, 'opp_date', group_f="partner_id", amount='opp_amount', year=True)
		s_labels = [sub["partner_id"] for sub in g_supplier]
		s_values = [sub['opp_amount'] for sub in g_supplier]

		# raggruppa per categoria
		g_category = dict_group_by(_list, 'opp_date', group_f="opp_category", amount='opp_amount',
								   year=True)
		c_labels = [sub["opp_category"] for sub in g_category]
		c_values = [sub['opp_category'] for sub in g_category]
	else:
		y_labels, y_values, s_labels, s_values, c_labels, c_values = [], [], [], [], [], []

	db.session.close()
	return render_template(
		VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL,
		site_detail=SITE_DETAIL, y_labels=json.dumps(y_labels), y_values=json.dumps(y_values),
		s_labels=json.dumps(s_labels), s_values=json.dumps(s_values),
		c_labels=json.dumps(c_labels), c_values=json.dumps(c_values)
	)


@opportunity_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['opportunities_admin', 'opportunities_write'])
def opportunity_create(p_id, s_id=None):
	"""Creazione Opportunità."""
	from app.organizations.plant.models import Plant

	from app.organizations.partners.models import Partner
	from app.organizations.partner_sites.models import PartnerSite

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	form = FormOpportunity.new(p_id=p_id)

	if request.method == 'POST' and form.validate():
		try:
			form_data = FormOpportunity(request.form).to_dict()
			# print('NEW_OPPORTUNITY:', json.dumps(form_data, indent=2))

			_time = datetime.now()

			new_opportunities = Opportunity(
				opp_activity=form_data['opp_activity'],
				opp_value=form_data['opp_value'],

				opp_date=form_data['opp_date'],
				opp_year=form_data['opp_year'],

				opp_description=form_data['opp_description'],
				opp_category=form_data['opp_category'],

				opp_status=form_data['opp_status'],

				opp_time_spent=None,

				opp_expiration_date=form_data['opp_expiration_date'],
				opp_expired=form_data['opp_expired'],

				opp_accountable=form_data['opp_accountable'],

				plant_id=form_data["plant_id"],
				plant_site_id=form_data["plant_site_id"],

				partner_id=form_data["partner_id"],
				partner_site_id=form_data["partner_site_id"],
				partner_contact_id=form_data["partner_contact_id"],

				note=form_data["note"],
				created_at=_time,
				updated_at=_time
			)

			Opportunity.create(new_opportunities)
			flash("OPPORTUNITA' creata correttamente.")

			if s_id not in [None, 0]:
				return redirect(url_for(PARTNER_SITE_DETAIL, _id=s_id))
			else:
				return redirect(url_for(PARTNER_DETAIL, _id=p_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form)
	else:
		# Estraggo dati azienda
		plant = Plant.query.get(1)
		form.plant_id.data = f'{plant.id} - {plant.organization}'
		# print('PLANT:', form.plant_id.data)

		# Estraggo dati fornitore
		partner = Partner.query.get(p_id)
		form.client_id.data = f'{partner.id} - {partner.organization}'
		# print('PARTNER:', form.supplier_id.data)

		if s_id:
			partner_site = PartnerSite.query.get(s_id)
			form.client_site_id.data = f'{partner_site.id} - {partner_site.organization}'
		# print('PARTNER_SITE:', form.supplier_site_id.data)

		return render_template(CREATE_HTML, form=form)


@opportunity_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['opportunities_admin', 'opportunities_read'])
def opportunity_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL
	from app.organizations.partner_contacts.routes import DETAIL_FOR as CONTACT_DETAIL

	# from app.invoices.invoice_rows.routes import (CREATE_FOR as INVOICE_ROW_CREATE, DETAIL_FOR as INVOICE_ROW_DETAIL,
	# 											  DELETE_FOR as INVOICE_ROW_DELETE)

	# Interrogo il DB
	opportunity = Opportunity.query \
		.options(joinedload(Opportunity.plant)) \
		.options(joinedload(Opportunity.plant_site)) \
		.options(joinedload(Opportunity.partner)) \
		.options(joinedload(Opportunity.partner_site)) \
		.options(joinedload(Opportunity.partner_contact)) \
		.options(joinedload(Opportunity.activity)) \
		.get(_id)

	_opportunity = opportunity.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = opportunity.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []
		
	# Attività
	_opportunity["opp_activity"] = f'{opportunity.activity.activity_code} - {opportunity.activity.activity_description}'

	# Organizzazione
	_opportunity["plant_id"] = f'{opportunity.plant.id} - {opportunity.plant.organization}'

	if opportunity.plant_site:
		_opportunity["plant_site_id"] = f'{opportunity.plant_site.id} - {opportunity.plant_site.organization}'

	# Partner
	_opportunity["partner_id"] = f'{opportunity.partner.id} - {opportunity.partner.organization}'
	p_id = opportunity.partner.id

	if opportunity.partner_site:
		_opportunity["partner_site_id"] = f'{opportunity.partner_site.id} - {opportunity.partner_site.site}'
		s_id = opportunity.partner_site.id
	else:
		s_id = None

	if opportunity.partner_contact:
		_opportunity["partner_site_id"] = f'{opportunity.partner_contact.id} - {opportunity.partner_contact.full_name}'
		c_id = opportunity.partner_contact.id
	else:
		c_id = None

	# # Estraggo la lista delle azioni
	# actions_list = opportunity.actions
	# if actions_list:
	# 	actions_list = [row.to_dict() for row in actions_list]
	# else:
	# 	actions_list = []
	#
	# # Calcolo totale
	# amount = opportunity.opp_value
	# if actions_list:
	# 	_opportunity["opp_value"] = 0
	# 	for row in actions_list:
	# 		_opportunity["opp_value"] = round(_opportunity["opp_value"] + row["act_value"], 2)
	# else:
	# 	_opportunity["opp_value"] = None

	# if amount != _opportunity["opp_value"]:
	# 	opportunity.opp_value = _opportunity["opp_value"]
	# 	Opportunity.update(_id, opportunity.to_dict())
	# 	flash("TOTALE OPPORTUNITA' aggiornato.")
	#
	# 	previous_data = opportunity.to_dict()
	# 	[previous_data.pop(key) for key in ["updated_at"]]
	# 	previous_data['opp_value'] = str(previous_data['opp_value'])
	#
	# 	from app.event_db.routes import event_create
	# 	_event = {
	# 		"username": session["user"]["username"],
	# 		"table": Opportunity.__tablename__,
	# 		"Modification": f"Update OPPORTUNITY whit id: {_id}",
	# 		"Previous_data": previous_data
	# 	}
	# 	_event = event_create(_event, opportunity_id=_id)

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_opportunity, view=VIEW_FOR, update=UPDATE_FOR,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		partner_detail=PARTNER_DETAIL, p_id=p_id,
		partner_site_detail=PARTNER_SITE_DETAIL, s_id=s_id,
		contact_detail=PARTNER_SITE_DETAIL, c_id=c_id,
		# rows_list=actions_list, r_len=len(actions_list),
	)


@opportunity_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['opportunities_admin', 'opportunities_write'])
def opportunity_update(_id):
	"""Aggiorna dati Opportunità."""
	from app.event_db.routes import event_create
	from app.invoices.activities.models import Activity

	# recupero i dati
	opportunity = Opportunity.query \
		.options(joinedload(Opportunity.plant)) \
		.options(joinedload(Opportunity.plant_site)) \
		.options(joinedload(Opportunity.partner)) \
		.options(joinedload(Opportunity.partner_site)) \
		.options(joinedload(Opportunity.partner_contact)) \
		.options(joinedload(Opportunity.activity)) \
		.get(_id)

	form = FormOpportunity.update(obj=opportunity, p_id=opportunity.plant_id)

	if request.method == 'POST' and form.validate():
		new_data = FormOpportunity(request.form).to_dict()

		previous_data = opportunity.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "invoice_pdf"]]
		previous_data['invoice_amount'] = str(previous_data['invoice_amount'])

		try:
			Opportunity.update(_id, new_data)
			flash("OPPORTUNITA' aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': opportunity.created_at,
				'updated_at': opportunity.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Opportunity.__tablename__,
			"Modification": f"Update OPPORTUNITY whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, opportunity_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		# Attività
		form.opp_activity = f'{opportunity.activity.activity_code} - {opportunity.activity.activity_description}'

		# Organizzazione
		form.plant_id.data = f'{opportunity.plant.id} - {opportunity.plant.organization}'
		form.plant_site_id.data = f'{opportunity.plant_site.id} - {opportunity.plant_site.site}' if opportunity.plant_site else None  # noqa

		# Fornitore
		form.client_id.data = f'{opportunity.client.id} - {opportunity.client.organization}'
		form.client_site_id.data = f'{opportunity.client_site.id} - {opportunity.client_site.site}' if opportunity.client_site else None  # noqa
		form.partner_contact_id.data = f'{opportunity.partner_contact_id.id} - {opportunity.partner_contact_id.full_name}' if opportunity.partner_contact_id else None  # noqa

		_info = {
			'created_at': opportunity.created_at,
			'updated_at': opportunity.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
