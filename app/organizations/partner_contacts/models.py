from app.app import db

# importazioni per creare relazioni in tabella
from app.organizations.partner_sites.models import PartnerSite  # noqa
from app.event_db.models import EventDB  # noqa


class PartnerContact(db.Model):
	# Table
	__tablename__ = 'partner_contacts'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	name = db.Column(db.String(25), index=True, unique=False, nullable=False)
	last_name = db.Column(db.String(50), index=True, unique=False, nullable=False)
	full_name = db.Column(db.String(80), index=True, unique=False, nullable=False)

	role = db.Column(db.String(50), index=False, unique=False, nullable=True)

	email = db.Column(db.String(80), index=False, unique=True, nullable=False)
	phone = db.Column(db.String(50), index=False, unique=False, nullable=True)

	partner_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)
	partner_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)

	partner = db.relationship('Partner', backref='partner_contacts', viewonly=True)
	partner_site = db.relationship('PartnerSite', backref='partner_contacts', viewonly=True)

	opportunities = db.relationship('Opportunity', backref='partner_contacts', lazy='dynamic')

	events = db.relationship('EventDB', backref='partner_contacts', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<PARTNER_CONTACT: [{self.id}] - {self.full_name}>'

	def __str__(self):
		return f'<PARTNER_CONTACT: [{self.id}] - {self.full_name}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		PartnerContact.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		site_id = self.partner_site_id or None

		return {
			'id': self.id,

			'name': self.name,
			'last_name': self.last_name,
			'full_name': self.full_name,

			'role': self.role,

			'partner_id': self.partner_id,
			'partner_site_id': site_id,

			'email': self.email,
			'phone': self.phone,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
