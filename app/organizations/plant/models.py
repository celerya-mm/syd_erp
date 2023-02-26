from app.app import db

# importazioni per creare relazioni in tabella
from app.organizations.plant_site.models import PlantSite  # noqa
from app.event_db.models import EventDB  # noqa
from app.account.models import User  # noqa


class Plant(db.Model):
	# Table
	__tablename__ = 'plants'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	organization = db.Column(db.String(80), index=True, unique=True, nullable=False)

	active = db.Column(db.Boolean, unique=False, nullable=True)
	site_type = db.Column(db.String(80), index=False, unique=False, nullable=True)

	email = db.Column(db.String(80), index=False, unique=True, nullable=False)
	pec = db.Column(db.String(80), index=False, unique=True, nullable=False)
	phone = db.Column(db.String(50), index=False, unique=False, nullable=False)

	address = db.Column(db.String(150), index=False, unique=False, nullable=True)
	cap = db.Column(db.String(5), index=False, unique=False, nullable=True)
	city = db.Column(db.String(55), index=False, unique=False, nullable=True)
	full_address = db.Column(db.String(210), index=False, unique=False, nullable=True)

	vat_number = db.Column(db.String(13), index=False, unique=False, nullable=False)
	fiscal_code = db.Column(db.String(13), index=False, unique=False, nullable=True)
	sdi_code = db.Column(db.String(7), index=False, unique=False, nullable=True)

	users = db.relationship('User', backref='plants', order_by='User.last_name.asc()', lazy='dynamic')
	plant_site = db.relationship('PlantSite', backref='plants', lazy='dynamic')
	events = db.relationship('EventDB', backref='plants', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<PLANT: [{self.id}] - {self.organization}>'

	def __str__(self):
		return f'<PLANT: [{self.id}] - {self.organization}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Plant.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		return {
			'id': self.id,
			'active': self.active,
			'organization': self.organization,

			'site_type': self.site_type,

			'email': self.email,
			'pec': self.pec,
			'phone': self.phone,

			'address': self.address,
			'cap': self.cap,
			'city': self.city,
			'full_address': self.full_address,

			'vat_number': self.vat_number,
			'fiscal_code': self.fiscal_code,
			'sdi_code': self.sdi_code,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f"),
		}
