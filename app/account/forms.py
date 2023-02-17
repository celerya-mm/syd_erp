from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional

from .functions import psw_verify, psw_contain_usr
from .models import User
from ..functions import mount_full_address, mount_full_name, status_true_false, not_empty


def list_user():
    records = User.query.all()
    _list = [x.to_dict() for x in records]
    _user = [d["username"] for d in _list if "username" in d]
    _email = [d["email"] for d in _list if "email" in d]
    return _user, _email


class FormUserCreate(FlaskForm):
    """Form dati signup account Utente."""
    username = StringField(
        'Username', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=40)], default=""
    )

    active = BooleanField("Attivo", false_values=(False, ))

    syd_user = StringField('User SYD', validators=[Length(min=3, max=25), Optional()])

    new_password_1 = PasswordField('Nuova Password', validators=[
        DataRequired("Campo obbligatorio!"), Length(min=8, max=64)])
    new_password_2 = PasswordField('Conferma Password', validators=[
        DataRequired("Campo obbligatorio!"), Length(min=8, max=64),
        EqualTo('new_password_1',
                message='Le due password inserite non corrispondono tra di loro. Riprova a inserirle!')])

    name = StringField('Nome', validators=[Length(min=3, max=25), Optional()])
    last_name = StringField('Cognome', validators=[Length(min=3, max=25), Optional()])

    email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
    phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()], default="+39 ")

    address = StringField('Indirizzo', validators=[Length(min=3, max=150), Optional()])
    cap = StringField('CAP', validators=[Length(min=5, max=5), Optional()])
    city = StringField('Città', validators=[Length(min=3, max=55), Optional()])

    note = StringField('Note', validators=[Length(max=255), Optional()])

    submit = SubmitField("SAVE")

    def __repr__(self):
        return f'<USER SIGNUP with username: {self.username}>'

    def __str__(self):
        return f'<USER SIGNUP with username: {self.username}>'

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

    name = StringField('Nome', validators=[Length(min=3, max=25), Optional()])
    last_name = StringField('Cognome', validators=[Length(min=3, max=25), Optional()])

    email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])
    phone = StringField('Telefono', validators=[Length(min=7, max=25), Optional()])

    address = StringField('Indirizzo', validators=[Length(min=3, max=150), Optional()])
    cap = StringField('CAP', validators=[Length(min=5, max=5), Optional()])
    city = StringField('Città', validators=[Length(min=3, max=55), Optional()])

    note = StringField('Note', validators=[Length(max=255)])

    submit = SubmitField("SAVE")

    def __repr__(self):
        return f'<UPDATE - username: {self.username}>'

    def __str__(self):
        return f'<UPDATE - username: {self.username}>'

    def to_dict(self):
        """Converte form in dict."""
        return {
            'username': self.username.data.strip().replace(" ", ""),
            'active': status_true_false(self.active.data),

            'name': self.name.data.strip(),
            'last_name': self.last_name.data.strip(),
            'full_name': mount_full_name(self.name.data, self.last_name.data),

            'address': self.address.data.strip(),
            'cap': self.cap.data.strip(),
            'city': self.city.data.strip(),
            'full_address': mount_full_address(self.address.data, self.cap.data, self.city.data),

            'email': self.email.data.strip().replace(" ", ""),
            'phone': self.phone.data.strip(),

            'note': not_empty(self.note.data.strip()),
            'updated_at': datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        }


class FormUserResetPsw(FlaskForm):
    """Form reset password utente."""
    email = EmailField('email', validators=[DataRequired("Campo obbligatorio!"), Email(), Length(max=80)])

    submit = SubmitField("SAVE")

    def __repr__(self):
        return f'<RESET PSW - email: {self.email}>'

    def __str__(self):
        return f'<RESET PSW - email: {self.email}>'

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
