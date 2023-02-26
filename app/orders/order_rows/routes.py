import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, serialize_dict, timer_func
from .forms import FormOdaRowUpdate, FormOdaRowCreate, list_partner_sites
from .models import OdaRow

oda_rows_bp = Blueprint(
	'oda_rows_bp', __name__,
	template_folder='templates',
	static_folder='static'
)


CREATE = "/create/<int:o_id>/<int:p_id>/<int:s_id>/"
CREATE_FOR = "oda_rows_bp.oda_rows_create"
CREATE_HTML = "oda_rows_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "oda_rows_bp.oda_rows_view_detail"
DETAIL_HTML = "oda_rows_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "oda_rows_bp.oda_rows_update"
UPDATE_HTML = "oda_rows_update.html"


@oda_rows_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['oda_rows_admin', 'oda_rows_write'])
def oda_rows_create(o_id, p_id, s_id=None):
	"""Creazione Item."""
	from app.orders.orders.routes import DETAIL_FOR as ORDER_DETAIL
	from app.orders.items.models import Item

	form = FormOdaRowCreate.new(p_id=p_id)
	if request.method == 'POST' and form.validate():
		try:
			form_data = json.loads(json.dumps(request.form))
			# print('NEW_ROWS:', json.dumps(form_data, indent=2))

			_code = form_data['item_code'].split(" - ")[0]

			_item = Item.query.filter_by(item_code=_code).first()
			# print("ITEM_ODA_ROW:", json.dumps(_item.to_dict(), indent=2))

			_time = datetime.now()

			new_p = OdaRow(
				item_code=_item.item_code,
				item_code_supplier=_item.item_code_supplier if _item.item_code_supplier else None,

				item_description=_item.item_description if _item.item_description else None,

				item_price=_item.item_price,
				item_price_discount=_item.item_price_discount if _item.item_price_discount else None,
				item_currency=_item.item_currency if _item.item_currency else None,

				item_quantity=_item.item_quantity_min if _item.item_quantity_min else None,
				item_quantity_um=_item.item_quantity_um if _item.item_quantity_um else None,

				item_amount=_item.item_quantity_min * _item.item_price if _item.item_quantity_min else None,

				oda_id=o_id,

				supplier_id=p_id,
				supplier_site_id=s_id if s_id not in [0, None] else None,

				note=None,
				created_at=_time,
				updated_at=_time
			)

			OdaRow.create(new_p)
			flash("ODA_ROW creata correttamente.")

			return redirect(url_for(ORDER_DETAIL, _id=o_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form)
	else:
		return render_template(CREATE_HTML, form=form, order_view=ORDER_DETAIL, o_id=o_id)


@oda_rows_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['oda_rows_admin', 'oda_rows_read'])
def oda_rows_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL
	from app.orders.orders.routes import DETAIL_FOR as ORDER_DETAIL

	# Interrogo il DB
	oda_row = OdaRow.query \
		.options(joinedload(OdaRow.supplier)) \
		.options(joinedload(OdaRow.supplier_site)).get(_id)

	_oda_row = oda_row.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = oda_row.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	_oda_row["supplier_id"] = f'{oda_row.supplier.id} - {oda_row.supplier.organization}'
	p_id = oda_row.supplier.id

	if oda_row.supplier_site:
		_oda_row["supplier_site_id"] = f'{oda_row.supplier_site.id} - {oda_row.supplier_site.site}'
		s_id = oda_row.supplier_site.id
	else:
		s_id = None

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_oda_row, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, 		h_len=len(history_list),
		partner_detail=PARTNER_DETAIL, 	p_id=p_id,
		site_detail=SITE_DETAIL, s_id=s_id,
		order_detail=ORDER_DETAIL
	)


@oda_rows_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['oda_rows_admin', 'oda_rows_write'])
def oda_rows_update(_id):
	"""Aggiorna dati Item."""
	from app.event_db.routes import event_create

	# recupero i dati
	oda_row = OdaRow.query \
		.options(joinedload(OdaRow.supplier)) \
		.options(joinedload(OdaRow.supplier_site)).get(_id)

	form = FormOdaRowUpdate.update(obj=oda_row, p_id=oda_row.supplier_id)

	if request.method == 'POST' and form.validate():
		new_data = FormOdaRowUpdate(request.form).to_dict()

		if new_data["item_price_discount"] == 100:
			new_data["item_amount"] = 0

		elif new_data["item_price_discount"] is not None and new_data["item_price_discount"] > 0:
			_tot = round(float(new_data["item_price"]) * float(new_data["item_quantity"]), 2)
			_discount = (100 - float(new_data["item_price_discount"])) / 100
			new_data["item_amount"] = round(float(_tot) * _discount, 2) if _discount else _tot

		else:
			new_data["item_amount"] = round(float(new_data["item_price"]) * float(new_data["item_quantity"]), 2)
			# print("NEW_DATA_ROW:", json.dumps(new_data, indent=2, default=serialize_dict))

		previous_data = oda_row.to_dict()
		previous_data.pop("updated_at")

		try:
			OdaRow.update(_id, new_data)
			flash("ODA_ROW aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': oda_row.created_at,
				'updated_at': oda_row.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": OdaRow.__tablename__,
			"Modification": f"Update ODA_ROW whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, oda_row_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		if oda_row.supplier_site:
			form.supplier_site_id.data = f'{oda_row.supplier_site.id} - {oda_row.supplier_site.site}'

		list_partner_sites(oda_row.supplier_id)

		_info = {
			'created_at': oda_row.created_at,
			'updated_at': oda_row.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR, o_id=form.oda_id.data)
