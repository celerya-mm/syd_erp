from datetime import datetime
from config import db
from ..functions import address_mount, mount_full_name


class User(db.Model):
	# Table
	__tablename__ = 'users'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(20), index=True, unique=True, nullable=False)
	password = db.Column(db.String(64), index=False, unique=False, nullable=False)  # 64 char for hash code

	active = db.Column(db.Boolean, unique=False, nullable=False)

	name = db.Column(db.String(50), index=False, unique=False, nullable=True)
	last_name = db.Column(db.String(50), index=False, unique=False, nullable=True)
	full_name = db.Column(db.String(101), index=False, unique=True, nullable=True)

	email = db.Column(db.String(80), index=False, unique=True, nullable=True)
	phone = db.Column(db.String(25), index=False, unique=False, nullable=True)

	address = db.Column(db.String(150), index=False, unique=False, nullable=True)
	cap = db.Column(db.String(5), index=False, unique=False, nullable=True)
	city = db.Column(db.String(55), index=False, unique=False, nullable=True)
	full_address = db.Column(db.String(255), index=False, unique=False, nullable=True)

	auth_tokens = db.relationship('AuthToken', backref='user_tokens', lazy=True)
	events = db.relationship('EventDB', backref='user_events', lazy=True)
	roles = db.relationship('Role', secondary='user_roles', backref='roles_user', lazy='dynamic', viewonly=True)

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<USER ID: {self.id}; username: {self.username}>'

	def __str__(self):
		return f'<USER ID: {self.id}; username: {self.username}>'

	def __init__(self, username, password=None, active=None, name=None, last_name=None, phone=None, email=None,
				 address=None, cap=None, city=None, auth_tokens=None, events=None, note=None):
		self.username = username
		self.password = password

		self.active = active

		self.name = name
		self.last_name = last_name
		self.full_name = mount_full_name(name, last_name)

		self.phone = phone
		self.email = email

		self.address = address
		self.cap = cap
		self.city = city
		self.full_address = address_mount(address, cap, city)

		self.auth_tokens = auth_tokens or []

		self.events = events or []

		self.note = note or None
		self.created_at = datetime.now()
		self.updated_at = datetime.now()

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update():  # noqa
		"""Salva le modifiche a un record."""
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str
		return {
			'id': self.id,
			'username': self.username,

			'phone': self.phone,
			'email': self.email,

			'name': self.name,
			'last_name': self.last_name,
			'full_name': mount_full_name(self.name, self.last_name),

			'address': self.address,
			'cap': self.cap,
			'city': self.city,
			'full_address': address_mount(self.address, self.cap, self.city),

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
