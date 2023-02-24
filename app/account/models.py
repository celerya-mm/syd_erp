from app.app import db

# importazioni per creare relazioni in tabella
from app.auth_token.models import AuthToken  # noqa
# from app.organizations.plant.models import Plant  # noqa
from app.organizations.plant_site.models import PlantSite  # noqa
from app.roles.models import Role  # noqa
from app.event_db.models import EventDB  # noqa


class User(db.Model):
	# Table
	__tablename__ = 'users'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(20), index=True, unique=True, nullable=False)

	password = db.Column(db.String(64), index=False, unique=False, nullable=False)  # 64 char for hash code
	psw_changed = db.Column(db.Boolean, unique=False, nullable=False)

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

	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=True)
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id'), nullable=True)

	plant_user = db.relationship('Plant', backref='user_plant', viewonly=True)
	plant_site_user = db.relationship('PlantSite', backref='user_plant_site', viewonly=True)

	auth_tokens = db.relationship('AuthToken', backref='users', order_by='AuthToken.id.desc()', lazy='dynamic')
	roles = db.relationship('Role', secondary='user_roles', backref='users', viewonly=True, lazy='dynamic')
	events = db.relationship('EventDB', backref='users', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<USER: [{self.id}] - {self.username}>'

	def __str__(self):
		return f'<USER: [{self.id}] - {self.username}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		User.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		return {
			'id': self.id,
			'username': self.username,

			'psw_changed': self.psw_changed,
			'active': self.active,

			'phone': self.phone,
			'email': self.email,

			'name': self.name,
			'last_name': self.last_name,
			'full_name': self.full_name,

			'address': self.address,
			'cap': self.cap,
			'city': self.city,
			'full_address': self.full_address,

			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
