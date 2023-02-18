from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError

from .models import Role
from ..account.models import User


def list_roles():
    _list = []
    try:
        records = Role.query.all()
        for r in records:
            _list.append(r.name)
        return _list
    except Exception as err:
        print(err)
        return _list


def list_Users():
    _list = []
    try:
        records = User.query.all()
        for r in records:
            if r.username == 'celerya_superuser':
                pass
            else:
                _list.append(f'{r.id} - {r.username}')
        return _list
    except Exception as err:
        print(err)
        return _list


class FormRoleCreate(FlaskForm):
    """Form dati signup account Utente."""
    name = StringField(
        'name', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=50)], default=""
    )

    submit = SubmitField("SAVE")

    def __repr__(self):
        return f'<ROLE_CREATED: {self.name}>'

    def __str__(self):
        return f'<ROLE_CREATED: {self.name}>'

    def validate_name(self, field):  # noqa
        """Verifica presenza name nella tabella del DB."""
        if field.data in list_roles():
            raise ValidationError("Nome regola già utilizzato.")


class FormRoleUpdate(FlaskForm):
    """Form di modifica dati account escluso password ed e-mail"""
    name = StringField('Nome', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=50)])

    submit = SubmitField("SAVE")

    def __repr__(self):
        return f'<ROLE_UPDATED: {self.name}>'

    def __str__(self):
        return f'<ROLE_UPDATED: {self.name}>'

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
