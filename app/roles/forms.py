from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError

from app.users.models import User
from app.app import db
from .models import Role


def list_roles():
	_list = []
	try:
		records = Role.query.order_by(Role.name.asc()).all()
		for r in records:
			_list.append(r.name)

		db.session.close()
		return _list
	except Exception as err:
		print('ERROR_LIST_ROLES', err)
		return _list


def list_Users():
	_list = []
	try:
		records = User.query.order_by(User.username.asc()).all()
		for r in records:
			if r.username == 'celerya_superuser':
				pass
			else:
				_list.append(f'{r.id} - {r.username}')

		db.session.close()
		return _list
	except Exception as err:
		print('ERROR_LIST_USERS', err)
		return _list


class FormRole(FlaskForm):
	"""Form dati signup account Utente."""
	name = StringField(
		'name', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=50)], default=""
	)

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ROLE: {self.name}>'

	def __str__(self):
		return f'<ROLE: {self.name}>'

	def validate_name(self, field):  # noqa
		"""Verifica presenza name nella tabella del DB."""
		if field.data in list_roles():
			raise ValidationError("Nome regola già utilizzato.")

	def to_dict(self):
		"""Converte form in dict."""
		return {
			'name': self.name.data,
			'updated_at': datetime.now()
		}


class FormRoleAddUser(FlaskForm):
	"""Form di modifica dati account escluso password ed e-mail"""
	username = SelectField('username', choices=list_Users())

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<ROLE_ADD_TO_USER: {self.username}>'

	def __str__(self):
		return f'<ROLE_ADD_TO_USER: {self.username}>'

	def to_dict(self):
		"""Converte form in dict."""
		return {
			'username': self.username.data,
		}
