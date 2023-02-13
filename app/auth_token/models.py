from datetime import datetime, timedelta

from ..app import db


def calc_expiration_token():
	"""Scadenza token per login gestionale."""
	_exp = datetime.now() + timedelta(days=1)
	_exp = _exp.replace(hour=0, minute=0, second=0, microsecond=0)
	return _exp


def calc_exp_token_reset_psw():
	"""Imposta scadenza a 15 min."""
	_exp = datetime.now() + timedelta(minutes=15)
	return _exp


class AuthToken(db.Model):
	# Table
	__tablename__ = 'auth_tokens'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	token = db.Column(db.String(36), nullable=False, unique=True)

	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	expires_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<AuthToken: {self.token}>'

	def __str__(self):
		return f'<AuthToken: {self.token}>'

	def __init__(self, token, user_id, expires_at=calc_expiration_token()):
		self.token = token
		self.user_id = user_id
		self.created_at = datetime.now()
		self.expires_at = expires_at

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update():  # noqa
		"""Salva le modifiche a un record."""
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from ..functions import date_to_str
		return {
			'id': self.id,
			'token': self.token,
			'user_id': self.user_id,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'expires_at': date_to_str(self.expires_at, "%Y-%m-%d %H:%M:%S.%f"),
		}
