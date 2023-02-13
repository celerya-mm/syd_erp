import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from config import db

from .forms import FormRuleCreate, FormRuleUpdate, FormRuleAddUser
from ..account.models import User
from ..functions import token_user_validate, access_required
from .models import Role, UserRoles

role_bp = Blueprint(
	'role_bp', __name__,
	template_folder='templates',
	static_folder='static'
)


VIEW = "/view/"
VIEW_FOR = "role_bp.role_view"
VIEW_HTML = "role_view.html"

CREATE = "/create/"
CREATE_FOR = "role_bp.role_create"
CREATE_HTML = "role_create.html"

HISTORY = "/view/history/<int:_id>"
HISTORY_FOR = "role_bp.role_view_history"
HISTORY_HTML = "role_view_history.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "role_bp.role_update"
UPDATE_HTML = "role_update.html"

ADD = "/add/role_to_user/<_id>/"
ADD_FOR = "role_bp.add_role_to_user"
ADD_HTML = "role_assign.html"

REMOVE = "/remove/role_to_user/<id_role>/<id_user>/"
REMOVE_FOR = "role_bp.remove_role_to_user"


@role_bp.route(VIEW, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin', 'roles_view'])
def role_view():
	"""Visualizzo informazioni User."""

	# Estraggo la lista dei permessi
	_list = Role.query.all()
	_list = [r.to_dict() for r in _list]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, update=UPDATE_FOR, history=HISTORY_FOR)


@role_bp.route(CREATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin'])
def role_create():
	"""Creazione Utente Consorzio."""
	form = FormRuleCreate()
	if form.validate_on_submit():
		form_data = json.loads(json.dumps(request.form))
		new_role = Role(
			name=form_data["name"].strip(),
		)
		try:
			Role.create(new_role)
			flash("REGOLA creata correttamente.")
			return redirect(url_for(VIEW_FOR))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(CREATE_HTML, form=form, view=VIEW_FOR)
	else:
		return render_template(CREATE_HTML, form=form, view=VIEW_FOR)


@role_bp.route(HISTORY, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin'])
def role_view_history(_id):
	"""Visualizzo il dettaglio del record."""
	from ..account.routes import HISTORY_FOR as USER_HISTORY_FOR

	# Interrogo il DB
	role = Role.query.get(_id)
	_role = role.to_dict()

	_user_list = []
	for u in role.user_roles:
		u = User.query.get(u.id)
		if u not in _user_list:
			_user_list.append(u)

	u_len = len(_user_list)

	db.session.close()
	return render_template(HISTORY_HTML, form=_role, users=_user_list, view=VIEW_FOR, update=UPDATE_FOR,
						   assign=ADD_FOR, user_history=USER_HISTORY_FOR, delete=REMOVE_FOR, u_len=u_len)


@role_bp.route(UPDATE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin'])
def role_update(_id):
	"""Aggiorna dati Record."""

	form = FormRuleUpdate()
	# recupero i dati
	role = Role.query.get(_id)

	if form.validate_on_submit():
		new_data = json.loads(json.dumps(request.form))

		role.name = new_data["name"].strip()
		role.updated_at = datetime.now()
		try:
			Role.update()
			flash("PERMESSO aggiornato correttamente.")
			return redirect(url_for(HISTORY_FOR, _id=_id))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': role.created_at,
				'updated_at': role.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=HISTORY_FOR)
	else:
		form.name.data = role.name

		_info = {
			'created_at': role.created_at,
			'updated_at': role.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=HISTORY_FOR)


@role_bp.route(ADD, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin'])
def add_role_to_user(_id):
	"""Aggiunge una regala a un utente."""

	form = FormRuleAddUser()

	if form.validate_on_submit():
		new_data = json.loads(json.dumps(request.form))
		new_user_role = UserRoles(
			user_id=new_data['username'].split(" - ")[0],
			role_id=_id
		)
		try:
			UserRoles.create(new_user_role)
			flash(f"Regola {_id} assegnata correttamente ad utente '{new_data['username'].split(' - ')[1]}'.")
			return redirect(url_for(HISTORY_FOR, _id=_id))
		except Exception as err:
			flash(err)
			return render_template(ADD_HTML, form=form, id=_id, history=HISTORY_FOR)
	else:
		return render_template(ADD_HTML, form=form, id=_id, history=HISTORY_FOR)


@role_bp.route(REMOVE, methods=["GET", "POST"])
@token_user_validate
@access_required(roles=['roles_admin'])
def remove_role_to_user(id_role, id_user):
	"""Rimuove una regala a un utente."""
	try:
		remove_data = UserRoles.query.filter_by(role_id=id_role, user_id=id_user).first()
		print('REMOVE:', json.dumps(remove_data.to_dict(), indent=2))
		UserRoles.remove(remove_data)
		flash(f'Regola {id_role} rimossa correttamente da utente {id_user}.')
		return redirect(url_for(HISTORY_FOR, _id=id_role))
	except Exception as err:
		flash(err)
		return redirect(url_for(HISTORY_FOR, _id=id_role))
