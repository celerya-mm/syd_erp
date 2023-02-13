import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy.exc import IntegrityError

from config import db
from app.app import session
from .models import EventDB

from ..account.models import User
from ..functions import token_user_validate, date_to_str


event_bp = Blueprint(
	'event_bp', __name__,
	template_folder='templates',
	static_folder='static'
)


HISTORY = "/event/view/history/<int:_id>/"
HISTORY_FOR = "event_bp.event_view_history"
HISTORY_HTML = "event_view_history.html"

RESTORE = "/event/restore/<int:_id>/<int:id_record>/<table>/<view_for>/"
RESTORE_FOR = "event_bp.event_restore"


def event_create(event, user_id=None):
	"""Registro evento DB."""
	try:
		new_event = EventDB(
			event=event,
			user_id=user_id,
		)

		EventDB.create(new_event)
		print("EVENT_CREATED.")
		return True
	except IntegrityError as err:
		db.session.close()
		if "duplicate key value violates unique constraint" in str(err):
			return True
		else:
			print("INTEGRITY_ERROR_EVENT:", str(err))
			flash(err)
			return str(err)
	except Exception as err:
		db.session.close()
		print("ERROR_REGISTR_EVENT:", str(err))
		flash(err)
		return str(err)


@event_bp.route(HISTORY, methods=["GET", "POST"])
@token_user_validate
def event_view_history(_id):
	"""Visualizzo la storia delle modifiche al record utente Administrator."""
	from ..account.routes import HISTORY_FOR as USER_HISTORY_FOR

	# Interrogo il DB
	event = EventDB.query.get(_id)
	_event = event.to_dict()

	# estraggo record collegato
	if event.user_id:
		related = User.query.get(event.user_id)
		related = related.to_dict()
		field = "user_id"
		table = User.__tablename__
		id_related = related["id"]
		type_related = "Utenti"
		view_related = USER_HISTORY_FOR
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
		HISTORY_HTML, form=_event, restore=RESTORE_FOR, table=table,
		history_list=history_list, h_len=len(history_list), view=HISTORY_FOR,
		id_related=id_related, view_related=view_related, type_related=type_related
	)


@event_bp.route(RESTORE, methods=["GET", "POST"])
@token_user_validate
def event_restore(_id, id_record, table, view_for):
	try:
		models = [User]
		model = next((m for m in models if m.__tablename__ == table), None)
		# print("TABLE_DB:", model, "ID:", id_record)
		if model:
			data = EventDB.query.get(_id)
			data = data.to_dict()
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
			return redirect(url_for(view_for, _id=id_record))
	except Exception as err:
		db.session.close()
		flash(f"ERROR: {err}")
		return redirect(url_for(view_for, _id=id_record))
