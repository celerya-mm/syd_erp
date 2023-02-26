import json
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from ..app import session, db
from .forms import FormUserLogin, FormUserCreate, FormUserUpdate, FormUserPswChange
from .functions import psw_hash
from .models import User
from ..auth_token.functions import __save_auth_token
from ..functions import (token_user_validate, access_required, access_required_update_psw, status_true_false,
						 mount_full_address, mount_full_name, timer_func, not_empty, serialize_dict)
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

UPDATE_PSW = "/update/psw/<int:_id>/"
UPDATE_PSW_FOR = "account_bp.user_update_password"
UPDATE_PSW_HTML = "user_update_password.html"


@account_bp.route("/login/", methods=["GET", "POST"])
@timer_func
def login():
	"""Effettua la log-in."""
	form = FormUserLogin()
	if form.validate_on_submit():
		_user = User.query.filter_by(username=form.username.data, password=psw_hash(str(form.password.data))).first()
		if _user:
			try:
				_token = _user.auth_tokens.first()
				if _token and _token.expires_at > datetime.now():
					token = _token.token
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

				session["user_roles"] = _roles
				# print('SESSION:', json.dumps(session, indent=2))
				db.session.close()

				if _user.psw_changed is not True:
					flash("Al primo accesso è richiesto il cambio della password assegnata dall'amministrazione.")
					return redirect(url_for(UPDATE_PSW_FOR, _id=_user.id))
				else:
					return redirect(url_for(VIEW_FOR))
			except Exception as err:
				flash(f'ERROR: {err}')
				return render_template("user_login.html", form=form)
		else:
			flash("Invalid username or password. Please try again!", category="alert")
			return render_template("user_login.html", form=form)
	else:
		return render_template("user_login.html", form=form)


@account_bp.route("/logout/")
@timer_func
def logout(msg=None):
	"""Effettua il log-out ed elimina i dati della sessione."""
	if msg:
		flash(msg)
	flash("Log-Out effettuato.")
	session.clear()
	return redirect(url_for('account_bp.login'))


@account_bp.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['users_admin', 'users_read'])
def user_view():
	"""Visualizzo informazioni Utente."""
	try:
		# Estraggo l'utente corrente
		user = User.query.get(session["user"]["id"])
		_admin = user.to_dict()

		# Estraggo la lista degli utenti
		_list = User.query.all()
		_list = [r.to_dict() for r in _list if r.username != 'celerya_superuser']

		db.session.close()
		return render_template(
			VIEW_HTML, admin=_admin, form=_list, create=CREATE_FOR, update=UPDATE_FOR, update_psw=UPDATE_PSW_FOR,
			detail=DETAIL_FOR
		)
	except Exception as err:
		flash(f'ERROR: {err}')
		return redirect(url_for('account_bp.login'))


@account_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['users_admin', 'users_write'])
def user_create():
	"""Creazione Utente personale."""
	form = FormUserCreate.new()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))

		_time = datetime.now()

		new_user = User(
			username=form_data["username"].replace(" ", ""),

			password=psw_hash(form_data["new_password_1"].replace(" ", "")),
			psw_changed=False,

			active=status_true_false(form_data["active"]),

			name=not_empty(form_data["name"].strip()),
			last_name=not_empty(form_data["last_name"].strip()),
			full_name=mount_full_name(
				form_data["name"].strip(), form_data["last_name"].strip()),

			email=form_data["email"].strip().replace(' ', ''),
			phone=not_empty(form_data["phone"].strip()),

			address=not_empty(form_data["address"].strip()),
			cap=not_empty(form_data["cap"]),
			city=not_empty(form_data["city"].strip().replace('  ', ' ')),
			full_address=mount_full_address(
				form_data["address"].strip(), form_data["cap"].strip(), form_data["city"].strip()),

			plant_id=form_data["plant_id"].split(' - ')[0],
			plant_site_id=form_data["plant_site_id"].split(' - ')[0] if form_data["plant_site_id"] else None,

			note=not_empty(form_data["note"].strip().replace('  ', ' ')),
			created_at=_time,
			updated_at=_time
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
@timer_func
@token_user_validate
@access_required(roles=['users_admin', 'users_read'])
def user_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL
	from app.organizations.plant.routes import DETAIL_FOR as PLANT_DETAIL
	from app.organizations.plant_site.routes import DETAIL_FOR as SITE_DETAIL
	from app.roles.routes import DETAIL_FOR as ROLE_DETAIL

	# Estraggo l' ID dell'utente corrente
	session["id_user"] = _id

	# Interrogo il DB
	user = User.query \
		.options(joinedload(User.plant_user)) \
		.options(joinedload(User.plant_site_user)) \
		.get(_id)

	_user = user.to_dict()

	_user["plant_id"] = \
		f'{user.plant_user.id} - {user.plant_user.organization}' if user.plant_user else None
	p_id = user.plant_user.id if user.plant_user else None

	_user["plant_site_id"] = \
		f'{user.plant_site_user.id} - {user.plant_site_user.organization}' if user.plant_site_user else None
	_user["plant_site_active"] = user.plant_site_user.active if user.plant_site_user else None
	s_id = user.plant_site_user.id if user.plant_site_user else None

	# Estraggo la storia delle modifiche per l'utente
	history_list = user.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Estraggo i ruoli assegnati all'utente
	roles_list = user.roles
	if roles_list:
		roles_list = [role.to_dict() for role in roles_list]
	else:
		roles_list = []

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_user, view=VIEW_FOR, update=UPDATE_FOR, update_psw=UPDATE_PSW_FOR,
		history_list=history_list, h_len=len(history_list), event_detail=EVENT_DETAIL,
		roles_list=roles_list, r_len=len(roles_list), role_detail=ROLE_DETAIL,
		plant_detail=PLANT_DETAIL, p_id=p_id,
		site_detail=SITE_DETAIL, s_id=s_id
	)


@account_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['users_admin', 'users_write'])
def user_update(_id):
	"""Aggiorna dati Utente."""
	from app.event_db.routes import event_create

	# recupero i dati
	user = User.query.filter_by(id=_id).options(
		joinedload(User.plant_user),
		joinedload(User.plant_site_user)
	).one()

	form = FormUserUpdate.update(obj=user)
	# print(json.dumps(user.to_dict(), indent=2, default=serialize_dict))

	if request.method == 'POST' and form.validate():
		new_data = FormUserUpdate(request.form).to_dict()
		# print("NEW_DATA_USER:", json.dumps(new_data, indent=2))

		previous_data = user.to_dict()
		previous_data.pop("updated_at")

		try:
			User.update(_id, new_data)
			session.pop('user_id')
			flash("UTENTE aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': user.created_at,
				'updated_at': user.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": User.__tablename__,
			"Modification": f"Update account USER whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, user_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		if user.plant_user:
			form.plant_id.data = f'{user.plant_user.id} - {user.plant_user.organization}'

		if user.plant_site_user:
			form.plant_site_id.data = f'{user.plant_site_user.id} - {user.plant_site_user.organization}'

		session['user_id'] = _id

		_info = {
			'created_at': user.created_at,
			'updated_at': user.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)


@account_bp.route(UPDATE_PSW, methods=["GET", "POST"])
@timer_func
@access_required_update_psw(roles=['users_admin', 'users_write'])
def user_update_password(_id, msg=None):
	"""Aggiorna password Utente."""
	from app.event_db.routes import event_create

	form = FormUserPswChange()
	if request.method == 'POST' and form.validate():
		form_data = json.loads(json.dumps(request.form))
		new_password = psw_hash(form_data["new_password_1"].replace(" ", "").strip())

		_user = User.query.get(_id)

		if new_password == _user.password:
			session.clear()
			flash("The 'New Password' inserted is equal to 'Registered Password'.")
			return render_template(UPDATE_PSW_HTML, form=form, id=_id, detail=DETAIL_FOR)
		else:
			_user.password = new_password
			_user.updated_at = datetime.now()
			_user.psw_changed = True

			db.session.commit()
			msg = f"PASSWORD utente {_user.username} resettata correttamente!"

			_event = {
				"executor": session['user']["username"],
				"username": _user.username,
				"Modification": "Password reset"
			}
			_event = event_create(_event, user_id=_id)
			return redirect(url_for('account_bp.logout', msg=msg))
	else:
		if session["user"]["id"] != _id and session["user"]["psw_changed"] is True:
			flash(f"Non hai i privilegi per effettuare il cambio password per l'utente con id: {_id}")
			flash(f"La password di un utente può essere cambiata solo dall'utente stesso.")
			return redirect(url_for(DETAIL_FOR, _id=_id))
		else:
			if msg is not None:
				flash(msg)
			return render_template(UPDATE_PSW_HTML, form=form, id=_id, detail=DETAIL_FOR)
