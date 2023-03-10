import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy.exc import IntegrityError

from app.app import db
from app.functions import token_user_validate, date_to_str, timer_func
from .models import EventDB

event_bp = Blueprint(
	'event_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = EventDB.__tablename__
BLUE_PRINT, B_PRINT = event_bp, 'event_bp'

DETAIL = "/view/detail/<int:_id>/"
DETAIL_FOR = f"{B_PRINT}.{TABLE}_view_detail"
DETAIL_HTML = f"{TABLE}_view_detail.html"

RESTORE = "/restore/<int:_id>/<int:id_record>/<table>/<view_for>/"
RESTORE_FOR = f"{B_PRINT}.{TABLE}_restore"


@timer_func
def events_db_create(
		event, user_id=None, partner_id=None, partner_contact_id=None, partner_site_id=None, item_id=None,
		order_id=None, plant_id=None, plant_site_id=None, oda_row_id=None, activity_id=None, invoice_id=None,
		invoice_row_id=None, opportunity_id=None, action_id=None
):
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
			oda_row_id=oda_row_id,

			plant_id=plant_id,
			plant_site_id=plant_site_id,

			activity_id=activity_id,
			invoice_id=invoice_id,
			invoice_row_id=invoice_row_id,

			opportunity_id=opportunity_id,
			action_id=action_id,

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


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
def events_db_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.users.models import User
	from app.users.routes import DETAIL_FOR as USER_DETAIL

	from app.organizations.plants.models import Plant
	from app.organizations.plants.routes import DETAIL_FOR as PLANT_DETAIL

	from app.organizations.plant_sites.models import PlantSite
	from app.organizations.plant_sites.routes import DETAIL_FOR as PLANT_SITE_DETAIL

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

	from app.invoices.activities.models import Activity
	from app.invoices.activities.routes import DETAIL_FOR as ACTIVITY_DETAIL

	from app.invoices.invoice.models import Invoice
	from app.invoices.invoice.routes import DETAIL_FOR as INVOICE_DETAIL

	from app.invoices.invoice_rows.models import InvoiceRow
	from app.invoices.invoice_rows.routes import DETAIL_FOR as INVOICE_ROW_DETAIL

	from app.business.opportunities.models import Opportunity
	from app.business.opportunities.routes import DETAIL_FOR as OPPORTUNITY_DETAIL
	
	from app.business.actions.models import Action
	from app.business.actions.routes import DETAIL_FOR as ACTION_DETAIL

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
		# Plant Site
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
		# Ordine Riga
		elif event.oda_row_id:
			related = OdaRow.query.get(event.oda_row_id)
			related = related.to_dict()
			field = "oda_row_id"
			table = OdaRow.__tablename__
			id_related = related["id"]
			type_related = "Order_Row"
			view_related = ORDER_ROW_DETAIL

		# Attivit??
		elif event.activity_id:
			related = Activity.query.get(event.activity_id)
			related = related.to_dict()
			field = "activity_id"
			table = Activity.__tablename__
			id_related = related["id"]
			type_related = "Activity"
			view_related = ACTIVITY_DETAIL
		# Fattura
		elif event.invoice_id:
			related = Invoice.query.get(event.invoice_id)
			related = related.to_dict()
			field = "invoice_id"
			table = Invoice.__tablename__
			id_related = related["id"]
			type_related = "Invoice"
			view_related = INVOICE_DETAIL
		# Fattura Riga
		elif event.invoice_row_id:
			related = InvoiceRow.query.get(event.invoice_row_id)
			related = related.to_dict()
			field = "invoice_row_id"
			table = InvoiceRow.__tablename__
			id_related = related["id"]
			type_related = "InvoiceRow"
			view_related = INVOICE_ROW_DETAIL

		# Opportunit??
		elif event.opportunity_id:
			related = Opportunity.query.get(event.opportunity_id)
			related = related.to_dict()
			field = "opportunity_id"
			table = Opportunity.__tablename__
			id_related = related["id"]
			type_related = "Opportunity"
			view_related = OPPORTUNITY_DETAIL
		# Azione
		elif event.action_id:
			related = Action.query.get(event.action_id)
			related = related.to_dict()
			field = "action_id"
			table = Action.__tablename__
			id_related = related["id"]
			type_related = "Action"
			view_related = ACTION_DETAIL
			
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


@BLUE_PRINT.route(RESTORE, methods=["GET", "POST"])
@timer_func
@token_user_validate
def events_db_restore(_id, id_record, table, view_for):
	from app.users.models import User

	from app.organizations.plants.models import Plant
	from app.organizations.plant_sites.models import PlantSite

	from app.organizations.partners.models import Partner
	from app.organizations.partner_contacts.models import PartnerContact
	from app.organizations.partner_sites.models import PartnerSite

	from app.orders.items.models import Item

	from app.orders.orders.models import Oda
	from app.orders.order_rows.models import OdaRow

	from app.invoices.activities.models import Activity
	from app.invoices.invoice.models import Invoice
	from app.invoices.invoice_rows.models import InvoiceRow

	from app.business.opportunities.models import Opportunity
	from app.business.actions.models import Action

	try:
		models = [
			User, Plant, PlantSite, Partner, PartnerContact, PartnerSite, Item, Oda, OdaRow, Activity, Invoice,
			InvoiceRow, Opportunity, Action
		]
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
			flash('Nessun dato da ripristinare.')
			return redirect(url_for(view_for, _id=id_record))
	except Exception as err:
		db.session.close()
		flash(f"ERROR: {err}")
		return redirect(url_for(view_for, _id=id_record))
