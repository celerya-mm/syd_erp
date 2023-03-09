import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, serialize_dict, timer_func  # noqa
from .forms import FormInvoiceRowUpdate, FormInvoiceRowCreate
from .models import InvoiceRow

invoice_rows_bp = Blueprint(
	'invoice_rows_bp', __name__,
	template_folder='templates',
	static_folder='static'
)


CREATE = "/create/<int:inv_id>/<int:c_id>/<int:s_id>/"
CREATE_FOR = "invoice_rows_bp.invoice_rows_create"
CREATE_HTML = "invoice_rows_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "invoice_rows_bp.invoice_rows_view_detail"
DETAIL_HTML = "invoice_rows_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "invoice_rows_bp.invoice_rows_update"
UPDATE_HTML = "invoice_rows_update.html"

DELETE = "/delete/<int:_id>/<int:inv_id>/"
DELETE_FOR = "invoice_rows_bp.invoice_rows_delete"


@invoice_rows_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['invoice_rows_admin', 'invoice_rows_write'])
def invoice_rows_create(inv_id, c_id, s_id=None):
	"""Creazione Riga Fattura."""
	from app.invoices.invoice.routes import DETAIL_FOR as INVOICE_DETAIL
	from app.invoices.activities.models import Activity

	form = FormInvoiceRowCreate.new()
	if request.method == 'POST' and form.validate():
		try:
			form_data = json.loads(json.dumps(request.form))
			# print('NEW_ROWS:', json.dumps(form_data, indent=2))

			_code = form_data['activity_code'].split(" - ")[0]

			_activity = Activity.query.filter_by(activity_code=_code).first()
			# print("INVOICE_ROW:", json.dumps(_activity.to_dict(), indent=2))

			_time = datetime.now()

			new_row = InvoiceRow(
				activity_code=_activity.activity_code,

				activity_description=_activity.activity_description if _activity.activity_description else None,

				activity_price=_activity.activity_price,
				activity_price_discount=None,
				activity_currency=_activity.activity_currency if _activity.activity_currency else None,

				activity_quantity=_activity.activity_quantity if _activity.activity_quantity else None,
				activity_quantity_um=_activity.activity_quantity_um if _activity.activity_quantity_um else None,

				invoice_id=inv_id,

				client_id=c_id,
				client_site_id=s_id if s_id not in [0, None] else None,

				note=None,
				created_at=_time,
				updated_at=_time
			)

			InvoiceRow.create(new_row)
			flash("INVOICE_ROW creata correttamente.")

			return redirect(url_for(INVOICE_DETAIL, _id=inv_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form)
	else:
		return render_template(CREATE_HTML, form=form, invoice_view=INVOICE_DETAIL, inv_id=inv_id)


@invoice_rows_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['invoice_rows_admin', 'invoice_rows_read'])
def invoice_rows_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL
	from app.invoices.invoice.routes import DETAIL_FOR as INVOICE_DETAIL

	# Interrogo il DB
	invoice_row = InvoiceRow.query \
		.options(joinedload(InvoiceRow.client)) \
		.options(joinedload(InvoiceRow.client_site)).get(_id)

	_invoice_row = invoice_row.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = invoice_row.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	_invoice_row["client_id"] = f'{invoice_row.client.id} - {invoice_row.client.organization}'
	p_id = invoice_row.client.id

	if invoice_row.client_site:
		_invoice_row["client_site_id"] = f'{invoice_row.client_site.id} - {invoice_row.client_site.site}'
		s_id = invoice_row.client_site.id
	else:
		s_id = None

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_invoice_row, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, 		h_len=len(history_list),
		partner_detail=PARTNER_DETAIL, 	p_id=p_id,
		site_detail=SITE_DETAIL, 		s_id=s_id,
		invoice_detail=INVOICE_DETAIL
	)


@invoice_rows_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['invoice_rows_admin', 'invoice_rows_write'])
def invoice_rows_update(_id):
	"""Aggiorna dati Riga Fattura."""
	from app.event_db.routes import event_create

	# recupero i dati
	invoice_row = InvoiceRow.query \
		.options(joinedload(InvoiceRow.client)) \
		.options(joinedload(InvoiceRow.client_site)).get(_id)

	form = FormInvoiceRowUpdate.update(obj=invoice_row, p_id=invoice_row.client_id)

	if request.method == 'POST' and form.validate():
		new_data = FormInvoiceRowUpdate(request.form).to_dict()

		previous_data = invoice_row.to_dict()
		previous_data.pop("updated_at")
		previous_data['activity_price'] = str(previous_data['activity_price'])
		previous_data['activity_amount'] = str(previous_data['activity_amount'])

		# lavoro cambio codice articolo
		if invoice_row.activity_code != new_data["activity_code"]:
			from app.invoices.activities.models import Activity

			flash("Cambiato codice Attività. Controlla la riga della Fattura.")

			_activity = Activity.query.filter_by(activity_code=new_data["activity_code"]).first()
			if _activity:
				new_data['activity_description'] = _activity.activity_description
				new_data['activity_price'] = _activity.activity_price
				new_data['activity_quantity'] = _activity.activity_quantity
				new_data['activity_quantity_um'] = _activity.activity_quantity_um
			else:
				new_data['activity_description'] = None
				new_data['activity_price'] = None
				new_data['activity_quantity'] = None
				new_data['activity_quantity_um'] = None

		try:
			InvoiceRow.update(_id, new_data)
			flash("INVOICE_ROW aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': invoice_row.created_at,
				'updated_at': invoice_row.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR,
								   inv_id=form.invoice_id.data)

		_event = {
			"username": session["user"]["username"],
			"table": InvoiceRow.__tablename__,
			"Modification": f"Update INVOICE_ROW whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, invoice_row_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		if invoice_row.client_site:
			form.client_site_id.data = f'{invoice_row.client_site.id} - {invoice_row.client_site.site}'

		_info = {
			'created_at': invoice_row.created_at,
			'updated_at': invoice_row.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR,
							   inv_id=form.invoice_id.data)


@invoice_rows_bp.route(DELETE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['invoice_rows_admin', 'invoice_rows_write'])
def invoice_rows_delete(_id, inv_id):
	"""Cancella Riga Fattura"""
	from app.invoices.invoice.routes import DETAIL_FOR as INVOICE_DETAIL
	try:
		InvoiceRow.remove(_id)
		flash(f'RIGA id [{_id}] FATTURA id [{inv_id}] rimossa correttamente.')
		return redirect(url_for(INVOICE_DETAIL, _id=inv_id))
	except Exception as err:
		flash(f'RIGA id [{_id}] FATTURA id [{inv_id}] NON rimossa: {err}.')
		return redirect(url_for(INVOICE_DETAIL, _id=inv_id))
