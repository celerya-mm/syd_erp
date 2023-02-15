import json
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from config import db
from .forms import FormUserLogin, FormUserCreate, FormUserUpdate, FormUserPswChange
from .functions import psw_hash
from .models import User
from ..auth_token.functions import __save_auth_token
from ..functions import token_user_validate, access_required, status_si_no, status_true_false
from ..roles.models import Role

account_bp = Blueprint(
	'account_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "account_bp.user_view"
VIEW_HTML = "user_view.html"

CREATE = "/create/"
CREATE_FOR = "account_bp.user_create"
CREATE_HTML = "user_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "account_bp.user_view_detail"
DETAIL_HTML = "user_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "account_bp.user_update"
UPDATE_HTML = "user_update.html"

UPDATE_PSW = "/update/psw/<int:_id>"
UPDATE_PSW_FOR = "account_bp.user_update_password"
UPDATE_PSW_HTML = "user_update_password.html"


@account_bp.route("/login/", methods=["GET", "POST"])
def login():
	"""Effettua la log-in."""
	form = FormUserLogin()
	if form.validate_on_submit():
		_user = User.query.filter_by(username=form.username.data, password=psw_hash(str(form.password.data))).first()
		if _user not in [None, ""]:
			record = _user.auth_tokens.first()
			if record and record.expires_at > datetime.now():
				token = record.token
			else:
				token = uuid4()
				_auth_token = __save_auth_token(token, _user.id)

			session.permanent = False
			session["token_login"] = token
			session["user"] = _user.to_dict()

			_roles = []
			for r in _user.roles:
				r = Role.query.get(r.id)
				if r not in _roles:
					_roles.append(r.name)

			# print('RULES:', _rules)
			session["user_roles"] = _roles

			db.session.close()
			return redirect(url_for(VIEW_FOR))

		else:
			flash("Invalid username or password. Please try again!", category="alert")
			return render_template("user_login.html", form=form)
	else:
		return render_template("user_login.html", form=form)


@account_bp.route("/logout/")
def logout():
	"""Effettua il log-out ed elimina i dati della sessione."""
	session.clear()
	flash("Log-Out effettuato.")
	return redirect(url_for('account_bp.login'))


@account_bp.route(VIEW, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['account_admin', 'account_read'])
def user_view():
	"""Visualizzo informazioni User."""
	# Estraggo l'utente corrente
	user = User.query.get(session["user"]["id"])
	_admin = user.to_dict()

	# Estraggo la lista degli utenti
	_list = User.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, admin=_admin, form=_list, create=CREATE_FOR, update=UPDATE_FOR,
						   update_psw=UPDATE_PSW_FOR, detail=DETAIL_FOR)


@account_bp.route(CREATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['account_admin', 'account_write'])
def user_create():
	"""Creazione Utente personale."""
	form = FormUserCreate()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))
		new_user = User(
			username=form_data["username"].replace(" ", ""),
			active=status_true_false(form_data["active"]),
			name=form_data["name"].strip(),
			last_name=form_data["last_name"].strip(),
			email=form_data["email"].strip(),
			phone=form_data["phone"].strip(),
			address=form_data["address"].strip(),
			cap=form_data["cap"].strip(),
			city=form_data["city"].strip(),
			password=psw_hash(form_data["new_password_1"].replace(" ", "")),
			note=form_data["note"].strip()
		)
		try:
			User.create(new_user)
			flash("UTENTE creato correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@account_bp.route(DETAIL, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['account_admin', 'account_read'])
def user_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL

	# Estraggo l' ID dell'utente corrente
	session["id_user"] = _id

	# Interrogo il DB
	user = User.query.get(_id)
	_user = user.to_dict()

	# Estraggo la storia delle modifiche per l'utente
	history_list = user.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_user, view=VIEW_FOR, update=UPDATE_FOR, update_psw=UPDATE_PSW_FOR,
		history_list=history_list, h_len=len(history_list), event_detail=EVENT_DETAIL,
	)


@account_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['account_admin', 'account_write'])
def user_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import event_create

	form = FormUserUpdate()
	# recupero i dati
	user = User.query.get(_id)

	if form.validate_on_submit():
		new_data = FormUserUpdate(request.form).to_dict()

		previous_data = user.to_dict()
		previous_data.pop("updated_at")

		user.username = new_data["username"]
		user.active = new_data["active"]

		user.name = new_data["name"]
		user.last_name = new_data["last_name"]
		user.full_name = new_data["full_name"]

		user.address = new_data["address"]
		user.cap = new_data["cap"]
		user.city = new_data["city"]
		user.full_address = new_data["full_address"]

		user.email = new_data["email"]
		user.phone = new_data["phone"]

		user.note = new_data["note"]
		user.updated_at = datetime.now()
		try:
			User.update()
			flash("UTENTE aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': user.created_at,
				'updated_at': user.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": User.__tablename__,
			"Modification": f"Update account USER whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, user_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		form.username.data = user.username
		form.active.data = status_si_no(user.active)
		form.name.data = user.name
		form.last_name.data = user.last_name
		form.email.data = user.email
		form.phone.data = user.phone
		form.address.data = user.address
		form.cap.data = user.cap
		form.city.data = user.city
		form.note.data = user.note

		_info = {
			'created_at': user.created_at,
			'updated_at': user.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)


@account_bp.route(UPDATE_PSW, methods=["GET", "POST"])
@access_required(roles=['account_admin', 'account_write'])
def user_update_password(_id):
	"""Aggiorna password Utente."""
	from app.event_db.routes import event_create

	form = FormUserPswChange()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))
		new_password = psw_hash(form_data["new_password_1"].replace(" ", "").strip())

		_user = User.query.get(_id)

		if new_password == _user.password:
			session.clear()
			flash("The 'New Password' inserted is equal to 'Registered Password'.")
			return render_template(UPDATE_PSW_HTML, form=form, id=_id, history=DETAIL_FOR)
		else:
			_user.password = new_password
			_user.updated_at = datetime.now()

			User.update()
			msg = f"PASSWORD utente {_user['username']} resettata correttamente!"

			_event = {
				"executor": session["username"],
				"username": _user["username"],
				"Modification": "Password reset"
			}
			_event = event_create(_event, user_id=_id)
			return msg
	else:
		if session["user"]["id"] != _id:
			flash(f"Non hai i privilegi per effettuare il cambio password per l'utente con id: {_id}")
			flash(f"La password di un utente può essere cambiata solo dall'utente stesso.")
			return redirect(url_for(DETAIL_FOR, _id=_id))
		else:
			return render_template(UPDATE_PSW_HTML, form=form, id=_id, history=DETAIL_FOR)
