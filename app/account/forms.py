from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional

from app.app import db, session
from .functions import psw_verify, psw_contain_usr
from .models import User
from ..functions import mount_full_address, mount_full_name, status_true_false, not_empty


def list_user():
	try:
		records = User.query.all()
		if 'user_id' in session.keys():
			_list = [x.to_dict() for x in records if x.id != session['user_id']]
		else:
			_list = [x.to_dict() for x in records]

		_user = [d["username"] for d in _list if "username" in d]
		_email = [d["email"] for d in _list if "email" in d]
		return _user, _email
	except Exception as err:
		print('ERROR:', err)
		return [], []


def list_plant_sites():
	from app.organizations.plant_site.models import PlantSite

	_list = ["-"]
	try:
		records = PlantSite.query.all()
		_dict = [x.to_dict() for x in records if x.active]
		db.session.close()
		for d in _dict:
			_list.append(f"{str(d['id'])} - {d['organization']}")
	except Exception as err:
		db.session.close()
		print(err)
		pass

	return _list


def list_plants():
	from app.organizations.plant.models import Plant

	_list = ["-"]
	try:
		records = Plant.query.all()
		_dict = [x.to_dict() for x in records if x.active]
		db.session.close()
		for d in _dict:
			_list.append(f"{str(d['id'])} - {d['organization']}")
	except Exception as err:
		db.session.close()
		print(err)
		pass

	return _list


class FormUserCreate(FlaskForm):
	"""Form dati signup account Utente."""
	username = StringField(
		'Username', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=40)], default=""
	)

	active = BooleanField("Attivo", false_values=(False, ))

	syd_user = StringField('User SYD', validators=[Optional(), Length(min=3, max=25)])

	new_password_1 = PasswordField('Nuova Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64)])
	new_password_2 = PasswordField('Conferma Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64),
		EqualTo('new_password_1',
				message='Le due password inserite non corrispondono tra di loro. Riprova a inserirle!')])

	name = StringField('Nome', validators=[Optional(), Length(min=3, max=25)])
	last_name = StringField('Cognome', validators=[Optional(), Length(min=3, max=25)])

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Optional(), Length(min=7, max=25)], default="+39 ")

	address = StringField('Indirizzo', validators=[Optional(), Length(min=3, max=150)])
	cap = StringField('CAP', validators=[Optional(), Length(min=5, max=5)])
	city = StringField('Città', validators=[Optional(), Length(min=3, max=55)])

	plant_id = SelectField("Sede Legale", validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField("Sede Operativa", validators=[Optional()])

	note = TextAreaField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<USER: {self.username}>'

	def __str__(self):
		return f'<USER: {self.username}>'

	@classmethod
	def new(cls):
		# Instantiate the form
		form = cls()
		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites()
		return form

	def validate_username(self, field):  # noqa
		"""Verifica presenza username nella tabella del DB."""
		if field.data in list_user()[0]:
			raise ValidationError("Username già utilizzato in tabella utenti.")

	def validate_email(self, field):  # noqa
		"""Verifica presenza email nella tabella del DB."""
		if field.data in list_user()[1]:
			raise ValidationError("Email già utilizzata in tabella utenti.")

	def validate_new_password_1(self, field):  # noqa
		"""Valida la nuova password."""
		message = psw_verify(field.data)
		if message:
			raise ValidationError(message)

		message = psw_contain_usr(field.data, self.username.data)
		if message:
			raise ValidationError(message)


class FormUserUpdate(FlaskForm):
	"""Form di modifica dati account escluso password ed e-mail"""
	username = StringField('Username', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=40)])

	active = BooleanField("Attivo")

	name = StringField('Nome', validators=[Optional()])
	last_name = StringField('Cognome', validators=[Optional()])

	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	phone = StringField('Telefono', validators=[Optional(), Length(min=7, max=25)])

	address = StringField('Indirizzo', validators=[Optional(), Length(min=3, max=150)])
	cap = StringField('CAP', validators=[Optional(), Length(min=5, max=5)])
	city = StringField('Città', validators=[Optional(), Length(min=3, max=55)])

	plant_id = SelectField("Sede Legale", validators=[DataRequired("Campo obbligatorio!")])
	plant_site_id = SelectField("Sede Operativa", validators=[Optional()])

	note = StringField('Note', validators=[Optional(), Length(max=255)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<UPDATE_USER - username: {self.username}>'

	def __str__(self):
		return f'<UPDATE_USER - username: {self.username}>'

	@classmethod
	def update(cls, obj):
		# Instantiate the form
		form = cls()
		form.username.data = obj.username
		form.active.data = obj.active

		form.name.data = obj.name if obj.name else None
		form.last_name.data = obj.last_name if obj.last_name else None

		form.email.data = obj.email if obj.email else None
		form.phone.data = obj.phone if obj.phone else None

		form.address.data = obj.address if obj.address else None
		form.cap.data = obj.cap if obj.cap else None
		form.city.data = obj.city if obj.city else None

		# Update the choices
		form.plant_id.choices = list_plants()
		form.plant_site_id.choices = list_plant_sites()

		form.note.data = obj.note if obj.note else None
		return form

	def validate_username(self, field):  # noqa
		"""Verifica presenza username nella tabella del DB."""
		if field.data in list_user()[0]:
			raise ValidationError("Username già utilizzato in tabella.")

	def validate_email(self, field):  # noqa
		"""Verifica presenza email nella tabella del DB."""
		if field.data in list_user()[1]:
			raise ValidationError("Email già utilizzata in tabella.")

	def to_dict(self):
		"""Converte form in dict."""
		return {
			'username': self.username.data.strip().replace(" ", ""),
			'active': status_true_false(self.active.data),

			'name': not_empty(self.name.data.strip()),
			'last_name': not_empty(self.last_name.data.strip()),
			'full_name': mount_full_name(self.name.data, self.last_name.data),

			'address': not_empty(self.address.data.strip()),
			'cap': not_empty(self.cap.data.strip()),
			'city': not_empty(self.city.data.strip()),
			'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

			'email': self.email.data.strip().replace(" ", ""),
			'phone': not_empty(self.phone.data).strip(),

			'plant_id': self.plant_id.data.split(' - ')[0] if self.plant_id.data not in ['-', None] else None,
			'plant_site_id': self.plant_site_id.data.split(' - ')[0] if self.plant_site_id.data not in ['-', None] else None,

			'note': not_empty(self.note.data.strip()),
			'updated_at': datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
		}


class FormUserResetPsw(FlaskForm):
	"""Form reset password utente."""
	email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])

	submit = SubmitField("SAVE")

	def __repr__(self):
		return f'<RESET_USER_PSW - email: {self.email}>'

	def __str__(self):
		return f'<RESET_USER_PSW - email: {self.email}>'

	def to_dict(self):
		"""Converte form in dict."""
		return {'email': self.email.data}


class FormUserLogin(FlaskForm):
	"""Form di login."""
	username = StringField('Username', validators=[DataRequired("Campo obbligatorio!"), Length(min=3)])
	password = PasswordField('Password', validators=[DataRequired("Campo obbligatorio!"), Length(min=8)])

	submit = SubmitField("LOGIN")


class FormUserInsertMail(FlaskForm):
	"""Form d'invio mail per reset password"""
	email = EmailField('Current e-mail', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
	submit = SubmitField("SEND_EMAIL")


class FormUserPswChange(FlaskForm):
	"""Form per cambio password"""
	old_password = PasswordField('Current Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64)])

	new_password_1 = PasswordField('Nuova Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64)])
	new_password_2 = PasswordField('Conferma Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64),
		EqualTo('new_password_1', message='Le password non corrispondono.')
	])

	submit = SubmitField("SEND_NEW_PASSWORD")


class FormPswReset(FlaskForm):
	"""Form per reset password"""
	new_password_1 = PasswordField('Nuova Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64)])
	new_password_2 = PasswordField('Conferma Password', validators=[
		DataRequired("Campo obbligatorio!"), Length(min=8, max=64),
		EqualTo('new_password_1', message='Le password non corrispondono.')
	])

	submit = SubmitField("SEND_NEW_PASSWORD")
