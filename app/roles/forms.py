from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError

from .models import Role
from ..account.models import User


def list_roles():
    records = Role.query.all()
    _list = [x.to_dict() for x in records]
    _name = [d["name"] for d in _list if "name" in d]
    return _name


def list_Users():
    records = User.query.all()
    _list = [x.to_dict() for x in records]
    _name = [f"{d['id']} - {d['username']}" for d in _list]
    return _name


class FormRuleCreate(FlaskForm):
    """Form dati signup account Utente."""
    name = StringField(
        'name', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=50)], default=""
    )

    submit = SubmitField("SIGNUP")

    def __repr__(self):
        return f'<RULE: {self.name}>'

    def __str__(self):
        return f'<RULE: {self.name}>'

    def validate_name(self, field):  # noqa
        """Verifica presenza name nella tabella del DB."""
        if field.data in list_roles():
            raise ValidationError("Nome regola già utilizzato.")


class FormRuleUpdate(FlaskForm):
    """Form di modifica dati account escluso password ed e-mail"""
    name = StringField('Nome', validators=[DataRequired("Campo obbligatorio!"), Length(min=3, max=50)])

    submit = SubmitField("MODIFICA")

    def __repr__(self):
        return f'<UPDATE_RULE - name: {self.name}>'

    def __str__(self):
        return f'<UPDATE_RULE - name: {self.name}>'

    def to_dict(self):
        """Converte form in dict."""
        return {
            'name': self.name.data,
        }


class FormRuleAddUser(FlaskForm):
    """Form di modifica dati account escluso password ed e-mail"""
    username = SelectField('username', choices=list_Users())

    submit = SubmitField("MODIFICA")

    def __repr__(self):
        return f'<USER: {self.username}>'

    def __str__(self):
        return f'<USER: {self.username}>'

    def to_dict(self):
        """Converte form in dict."""
        return {
            'username': self.username.data,
        }
