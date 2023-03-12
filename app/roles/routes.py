import json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError

from app.app import db, session
from .forms import FormRole, FormRoleAddUser
from .models import Role, UserRoles
from ..users.models import User
from ..functions import token_user_validate, access_required, timer_func

role_bp = Blueprint(
	'role_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = 'roles'
BLUE_PRINT, B_PRINT = role_bp, 'role_bp'

VIEW = "/view/"
VIEW_FOR = f"{B_PRINT}.{TABLE}_view"
VIEW_HTML = f"{TABLE}_view.html"

CREATE = "/create/"
CREATE_FOR = f"{B_PRINT}.{TABLE}_create"
CREATE_HTML = f"{TABLE}_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = f"{B_PRINT}.{TABLE}_view_detail"
DETAIL_HTML = f"{TABLE}_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = f"{B_PRINT}.{TABLE}_update"
UPDATE_HTML = f"{TABLE}_update.html"

ADD = "/add/role_to_user/<_id>/"
ADD_FOR = f"{B_PRINT}.{TABLE}_add_to_user"
ADD_HTML = f"{TABLE}_assign.html"

REMOVE = "/remove/role_to_user/<id_role>/<id_user>/"
REMOVE_FOR = f"{B_PRINT}.{TABLE}_remove_to_user"


@BLUE_PRINT.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def roles_view():
	"""Visualizzo informazioni User."""

	# Estraggo la lista dei permessi
	_list = Role.query.all()
	if 'superuser' in session['user_roles']:
		_list = [r.to_dict() for r in _list]
	else:
		_list = [r.to_dict() for r in _list if r.name != 'superuser']

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, update=UPDATE_FOR, detail=DETAIL_FOR)


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def roles_create():
	"""Creazione Utente Consorzio."""
	form = FormRole()
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


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def roles_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from ..users.routes import DETAIL_FOR as USER_DETAIL_FOR

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
	return render_template(DETAIL_HTML, form=_role, users=_user_list, view=VIEW_FOR, update=UPDATE_FOR,
						   assign=ADD_FOR, user_detail=USER_DETAIL_FOR, delete=REMOVE_FOR, u_len=u_len)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def roles_update(_id):
	"""Aggiorna dati Record."""
	# recupero i dati
	role = Role.query.get(_id)
	form = FormRole(obj=role)

	if request.method == 'POST' and form.validate():
		new_data = FormRole(request.form).to_dict()
		try:
			Role.update(_id, new_data)
			flash("REGOLA aggiornata correttamente.")
			return redirect(url_for(DETAIL_FOR, _id=_id))
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': role.created_at,
				'updated_at': role.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)
	else:
		_info = {
			'created_at': role.created_at,
			'updated_at': role.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, detail=DETAIL_FOR)


@BLUE_PRINT.route(ADD, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin'])
def roles_add_to_user(_id):
	"""Aggiunge una regala a un utente."""

	form = FormRoleAddUser()

	if form.validate_on_submit():
		new_data = json.loads(json.dumps(request.form))
		new_user_role = UserRoles(
			user_id=new_data['username'].split(" - ")[0],
			role_id=_id
		)
		try:
			UserRoles.create(new_user_role)
			flash(f"Regola {_id} assegnata correttamente ad utente '{new_data['username'].split(' - ')[1]}'.")
			return redirect(url_for(DETAIL_FOR, _id=_id))
		except Exception as err:
			flash(err)
			return render_template(ADD_HTML, form=form, id=_id, detail=DETAIL_FOR)
	else:
		return render_template(ADD_HTML, form=form, id=_id, detail=DETAIL_FOR)


@BLUE_PRINT.route(REMOVE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_delete'])
def roles_remove_to_user(id_role, id_user):
	"""Rimuove una regala a un utente."""
	try:
		remove_data = UserRoles.query.filter_by(role_id=id_role, user_id=id_user).first()
		print('REMOVE:', json.dumps(remove_data.to_dict(), indent=2))
		UserRoles.remove(remove_data)
		flash(f'Regola {id_role} rimossa correttamente da utente {id_user}.')
		return redirect(url_for(DETAIL_FOR, _id=id_role))
	except Exception as err:
		flash(err)
		return redirect(url_for(DETAIL_FOR, _id=id_role))
