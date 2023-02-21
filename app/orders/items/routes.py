import json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db
from app.functions import token_user_validate, access_required, not_empty
from .forms import FormItem
from .models import Item
from app.organizations.partner_sites.models import PartnerSite
from app.organizations.partners.models import Partner

item_bp = Blueprint(
	'item_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "item_bp.item_view"
VIEW_HTML = "item_view.html"

CREATE = "/create/<int:p_id>/<int:s_id>/"
CREATE_FOR = "item_bp.item_create"
CREATE_HTML = "item_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "item_bp.item_view_detail"
DETAIL_HTML = "item_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "item_bp.item_update"
UPDATE_HTML = "item_update.html"


@item_bp.route(VIEW, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['items_admin', 'items_read'])
def item_view():
	"""Visualizzo informazioni Items."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	# Estraggo la lista dei partners
	_list = Item.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL,
						   site_detail=SITE_DETAIL)


@item_bp.route(CREATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['items_admin', 'items_write'])
def item_create(p_id, s_id=None):
	"""Creazione Item."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	form = FormItem.new()
	if request.method == 'POST' and form.validate():
		try:
			form_data = json.loads(json.dumps(request.form))
			print('NEW_CONTACT:', json.dumps(form_data, indent=2))

			new_p = Item(
				item_code=form_data['item_code'],
				item_code_supplier=not_empty(form_data['item_code_supplier'].strip().replace('  ', ' ')),

				item_description=form_data['item_description'].strip().replace('  ', ' '),

				item_price=form_data['item_price'],
				item_price_discount=not_empty(form_data['item_price_discount']),
				item_currency=form_data['item_currency'],

				item_quantity_min=not_empty(form_data["item_quantity_min"]),
				item_quantity_um=not_empty(form_data["item_quantity_um"]),

				supplier_id=form_data["supplier_id"].split(' - ')[0],
				supplier_site_id=not_empty(form_data["supplier_site_id"].split(' - ')[0]),

				note=not_empty(form_data["note"])
			)
			Item.create(new_p)

			flash("ITEM creato correttamente.")

			if s_id not in [None, 0]:
				return redirect(url_for(SITE_DETAIL, _id=s_id))
			else:
				return redirect(url_for(PARTNER_DETAIL, _id=p_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, partner_view=PARTNER_DETAIL, p_id=p_id,
								   site_view=SITE_DETAIL, s_id=s_id)
	else:
		# setto il nuovo codice_articolo
		last_id = Item.query.order_by(Item.id.desc()).first()
		if last_id is None:
			form.item_code.data = 'itm_0001'
		else:
			form.item_code.data = f'itm_{str(int(last_id.id) + 1).zfill(4)}'

		partner = Partner.query.get(p_id)
		form.supplier_id.data = f'{partner.id} - {partner.organization}'
		# print('PARTNER:', form.partner_id.data)

		if s_id not in [None, 0]:
			site = PartnerSite.query.get(s_id)
			form.supplier_site_id.data = f'{site.id} - {site.site}'
			# print('SITE:', form.partner_site_id.data)

		return render_template(CREATE_HTML, form=form, partner_view=PARTNER_DETAIL, p_id=p_id,
							   site_view=SITE_DETAIL, s_id=s_id)


@item_bp.route(DETAIL, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['items_admin', 'items_read'])
def item_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	# Interrogo il DB
	item = Item.query \
		.options(joinedload(Item.supplier)) \
		.options(joinedload(Item.supplier_site)).get(_id)
	_item = item.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = item.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	_item["supplier_id"] = f'{item.supplier.id} - {item.supplier.organization}'
	p_id = item.supplier.id

	if item.supplier_site:
		_item["supplier_site_id"] = f'{item.supplier_site.id} - {item.supplier_site.site}'
		s_id = item.supplier_site.id
	else:
		s_id = None

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_item, view=VIEW_FOR, update=UPDATE_FOR, event_detail=EVENT_DETAIL,
		history_list=history_list, h_len=len(history_list), partner_detail=PARTNER_DETAIL, p_id=p_id,
		site_detail=SITE_DETAIL, s_id=s_id
	)


@item_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['items_admin', 'items_write'])
def item_update(_id):
	"""Aggiorna dati Item."""
	from app.event_db.routes import event_create

	# recupero i dati
	item = Item.query \
		.options(joinedload(Item.supplier)) \
		.options(joinedload(Item.supplier_site)).get(_id)
	form = FormItem.update(obj=item)

	if request.method == 'POST' and form.validate():
		new_data = FormItem(request.form).to_dict()

		previous_data = item.to_dict()
		previous_data.pop("updated_at")

		try:
			Item.update(_id, new_data)
			flash("ITEM aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': item.created_at,
				'updated_at': item.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Item.__tablename__,
			"Modification": f"Update ITEM whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, item_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		form.supplier_id.data = f'{item.supplier.id} - {item.supplier.organization}'
		if item.supplier_site:
			form.supplier_site_id.data = f'{item.supplier_site.id} - {item.supplier_site.site}'

		_info = {
			'created_at': item.created_at,
			'updated_at': item.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)
