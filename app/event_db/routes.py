import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy.exc import IntegrityError

from ..app import db
from .models import EventDB

from app.functions import token_user_validate, date_to_str, timer_func


event_bp = Blueprint(
	'event_bp', __name__,
	template_folder='templates',
	static_folder='static'
)


DETAIL = "/event/view/detail/<int:_id>/"
DETAIL_FOR = "event_bp.event_view_detail"
DETAIL_HTML = "event_view_detail.html"

RESTORE = "/event/restore/<int:_id>/<int:id_record>/<table>/<view_for>/"
RESTORE_FOR = "event_bp.event_restore"


@timer_func
def event_create(event, user_id=None, partner_id=None, partner_contact_id=None, partner_site_id=None, item_id=None,
				 order_id=None, plant_id=None, plant_site_id=None, oda_row_id=None):
	"""Registro evento DB."""
	try:
		new_event = EventDB(
			event=event,
			user_id=user_id,
			partner_id=partner_id,
			partner_contact_id=partner_contact_id,
			partner_site_id=partner_site_id,
			item_id=item_id,
			order_id=order_id,
			plant_id=plant_id,
			plant_site_id=plant_site_id,
			oda_row_id=oda_row_id,
			created_at=datetime.now()
		)

		EventDB.create(new_event)
		print("EVENT_CREATED.")
		return True
	except IntegrityError as err:
		db.session.close()
		if "duplicate key value violates unique constraint" in str(err):
			print("EVENT_DUPLICATED.")
			return True
		else:
			print("EVENT_INTEGRITY_ERROR:", str(err))
			flash(err)
			return str(err)
	except Exception as err:
		db.session.close()
		print("EVENT_CREATE_ERROR:", str(err))
		flash(err)
		return str(err)


@event_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
def event_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.account.models import User
	from app.account.routes import DETAIL_FOR as USER_DETAIL

	from app.organizations.plant.models import Plant
	from app.organizations.plant.routes import DETAIL_FOR as PLANT_DETAIL

	from app.organizations.plant_site.models import PlantSite
	from app.organizations.plant_site.routes import DETAIL_FOR as PLANT_SITE_DETAIL

	from app.organizations.partners.models import Partner
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL

	from app.organizations.partner_contacts.models import PartnerContact
	from app.organizations.partner_contacts.routes import DETAIL_FOR as PARTNER_CONTACT_DETAIL

	from app.organizations.partner_sites.models import PartnerSite
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	from app.orders.items.models import Item
	from app.orders.items.routes import DETAIL_FOR as ITEM_DETAIL

	from app.orders.orders.models import Oda
	from app.orders.orders.routes import DETAIL_FOR as ORDER_DETAIL

	from app.orders.order_rows.models import OdaRow
	from app.orders.order_rows.routes import DETAIL_FOR as ORDER_ROW_DETAIL

	# Interrogo il DB
	event = EventDB.query.get(_id)
	_event = event.to_dict()

	# estraggo record collegato
	try:
		# Utente
		if event.user_id:
			related = User.query.get(event.user_id)
			related = related.to_dict()
			field = "user_id"
			table = User.__tablename__
			id_related = related["id"]
			type_related = "Utenti"
			view_related = USER_DETAIL
		# Plant
		elif event.plant_id:
			related = Plant.query.get(event.plant_id)
			related = related.to_dict()
			field = "plant_id"
			table = Plant.__tablename__
			id_related = related["id"]
			type_related = "Plant"
			view_related = PLANT_DETAIL
		# Plant
		elif event.plant_site_id:
			related = PlantSite.query.get(event.plant_site_id)
			related = related.to_dict()
			field = "plant_site_id"
			table = PlantSite.__tablename__
			id_related = related["id"]
			type_related = "Plant_Site"
			view_related = PLANT_SITE_DETAIL
		# Partner
		elif event.partner_id:
			related = Partner.query.get(event.partner_id)
			related = related.to_dict()
			field = "partner_id"
			table = Partner.__tablename__
			id_related = related["id"]
			type_related = "Partner"
			view_related = PARTNER_DETAIL
		# Contatto Partner
		elif event.partner_contact_id:
			related = PartnerContact.query.get(event.partner_contact_id)
			related = related.to_dict()
			field = "partner_contact_id"
			table = PartnerContact.__tablename__
			id_related = related["id"]
			type_related = "Partner_Contact"
			view_related = PARTNER_CONTACT_DETAIL
		# Sito Partner
		elif event.partner_site_id:
			related = PartnerSite.query.get(event.partner_site_id)
			related = related.to_dict()
			field = "partner_site_id"
			table = PartnerSite.__tablename__
			id_related = related["id"]
			type_related = "Partner_Site"
			view_related = PARTNER_SITE_DETAIL
		# Articolo
		elif event.item_id:
			related = Item.query.get(event.item_id)
			related = related.to_dict()
			field = "item_id"
			table = Item.__tablename__
			id_related = related["id"]
			type_related = "Item"
			view_related = ITEM_DETAIL
		# Ordine
		elif event.order_id:
			related = Oda.query.get(event.order_id)
			related = related.to_dict()
			field = "order_id"
			table = Oda.__tablename__
			id_related = related["id"]
			type_related = "Order"
			view_related = ORDER_DETAIL
		# Ordine
		elif event.oda_row_id:
			related = OdaRow.query.get(event.oda_row_id)
			related = related.to_dict()
			field = "oda_row_id"
			table = OdaRow.__tablename__
			id_related = related["id"]
			type_related = "Order_Row"
			view_related = ORDER_ROW_DETAIL
		else:
			db.session.close()
			msg = "Nessun record trovato"
			return msg

		# Estraggo la storia delle modifiche del record di origine
		history_list = EventDB.query.filter(getattr(EventDB, field) == int(id_related), EventDB.id != int(_id)).all()
		history_list = [history.to_dict() for history in history_list]

		_event = json.loads(json.dumps(_event))

		db.session.close()
		return render_template(
			DETAIL_HTML, form=_event, restore=RESTORE_FOR, table=table,
			history_list=history_list, h_len=len(history_list), view_detail=DETAIL_FOR,
			id_related=id_related, view_related=view_related, type_related=type_related
		)
	except Exception as err:
		return f'ERROR_VIEW_EVENT: {err}'


@event_bp.route(RESTORE, methods=["GET", "POST"])
@timer_func
@token_user_validate
def event_restore(_id, id_record, table, view_for):
	from app.account.models import User
	from app.organizations.plant.models import Plant
	from app.organizations.plant_site.models import PlantSite
	from app.organizations.partners.models import Partner
	from app.organizations.partner_contacts.models import PartnerContact
	from app.organizations.partner_sites.models import PartnerSite
	from app.orders.items.models import Item
	try:
		models = [User, Plant, PlantSite, Partner, PartnerContact, PartnerSite, Item]
		model = next((m for m in models if m.__tablename__ == table), None)
		# print("TABLE_DB:", model, "ID:", id_record)
		if model:
			data = EventDB.query.get(_id)
			data = data.to_dict()
			if "Previous_data" in data["event"].keys():
				data = data["event"]["Previous_data"]
				# print("UPDATE_DATA:", json.dumps(data, indent=2), "TYPE:", type(data))
				updated_at = data["created_at"]
				data["updated_at"] = date_to_str(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")
				data.pop("id")

				# converto boolean
				for k, v in data.items():
					if v == "SI" or v == "si":
						data[k] = True
					elif v == "NO" or v == "no":
						data[k] = False
					else:
						pass

				try:
					record = model.query.get(id_record)
					# print("DATA_FROM_DB:", json.dumps(record.to_dict(), indent=2), "TYPE:", type(data))
					for k, v in data.items():
						setattr(record, k, v)
					db.session.commit()
					flash(f"Record ripristinato correttamente alla situazione precedente il: {updated_at}.")
					return redirect(url_for(view_for, _id=id_record))
				except IntegrityError as err:
					db.session.rollback()
					db.session.close()
					flash(f"ERRORE: {str(err.orig)}")
					return redirect(url_for(view_for, _id=id_record))
			else:
				flash('Nessun dato da ripristinare.')
				return redirect(url_for(view_for, _id=id_record))
		else:
			return redirect(url_for(view_for, _id=id_record))
	except Exception as err:
		db.session.close()
		flash(f"ERROR: {err}")
		return redirect(url_for(view_for, _id=id_record))
