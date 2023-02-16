from datetime import datetime
from config import db
from app.functions import date_to_str, mount_full_name


class Contact(db.Model):
	# Table
	__tablename__ = 'contacts'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	name = db.Column(db.String(25), index=True, unique=False, nullable=False)
	last_name = db.Column(db.String(50), index=True, unique=False, nullable=False)
	full_name = db.Column(db.String(80), index=True, unique=False, nullable=False)

	role = db.Column(db.String(50), index=False, unique=False, nullable=True)

	email = db.Column(db.String(80), index=False, unique=True, nullable=False)
	phone = db.Column(db.String(25), index=False, unique=False, nullable=True)

	partner_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)

	events = db.relationship('EventDB', backref='contact_events', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<CONTACT: [{self.id}] - {self.full_name}>'

	def __str__(self):
		return f'<CONTACT: [{self.id}] - {self.full_name}>'

	def __init__(self, name, last_name, role, email, phone, partner_id, events=None, note=None):
		self.name = name.strip().replace('  ', ' ')
		self.last_name = last_name.strip().replace('  ', ' ')
		self.full_name = mount_full_name(self.name, self.last_name)

		self.role = role

		self.email = email.strip().replace(' ', '')
		self.phone = phone.strip()

		self.partner_id = partner_id.split(' - ')[0]

		self.events = events or []

		self.note = note or None
		self.created_at = datetime.now()
		self.updated_at = datetime.now()

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Contact.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		return {
			'id': self.id,

			'name': self.name,
			'last_name': self.last_name,
			'full_name': mount_full_name(self.name, self.last_name),

			'role': self.role,

			'partner_id': self.partner_id,

			'email': self.email,
			'phone': self.phone,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
