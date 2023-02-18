from datetime import datetime
from config import db
from app.functions import mount_full_address, date_to_str

# importazioni per creare relazioni in tabella
from app.organizations.partner_contacts.models import PartnerContact  # noqa
from app.organizations.partner_sites.models import PartnerSite  # noqa
from app.orders.items.models import Item  # noqa
from app.event_db.models import EventDB  # noqa


class Partner(db.Model):
	# Table
	__tablename__ = 'partners'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	organization = db.Column(db.String(80), index=True, unique=True, nullable=False)

	client = db.Column(db.Boolean, unique=False, nullable=True)
	supplier = db.Column(db.Boolean, unique=False, nullable=True)
	partner = db.Column(db.Boolean, unique=False, nullable=True)

	email = db.Column(db.String(80), index=False, unique=True, nullable=False)
	pec = db.Column(db.String(80), index=False, unique=True, nullable=False)
	phone = db.Column(db.String(25), index=False, unique=False, nullable=False)

	address = db.Column(db.String(150), index=False, unique=False, nullable=True)
	cap = db.Column(db.String(5), index=False, unique=False, nullable=True)
	city = db.Column(db.String(55), index=False, unique=False, nullable=True)
	full_address = db.Column(db.String(210), index=False, unique=False, nullable=True)

	vat_number = db.Column(db.String(13), index=False, unique=False, nullable=False)
	fiscal_code = db.Column(db.String(13), index=False, unique=False, nullable=True)
	sdi_code = db.Column(db.String(7), index=False, unique=False, nullable=True)

	contacts = db.relationship(
		'PartnerContact', backref='partners', order_by='PartnerContact.last_name.asc()', lazy='dynamic')

	sites = db.relationship(
		'PartnerSite', backref='partners', lazy='dynamic')

	items = db.relationship(
		'Item', backref='partners', lazy='dynamic')

	events = db.relationship(
		'EventDB', backref='partners', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<PARTNER: [{self.id}] - {self.organization}>'

	def __str__(self):
		return f'<PARTNER: [{self.id}] - {self.organization}>'

	def __init__(self, organization, client, supplier, partner, email, pec, phone, address, cap, city, vat_number,
				 fiscal_code, sdi_code=None, events=None, note=None):
		self.organization = organization

		self.client = client
		self.supplier = supplier
		self.partner = partner

		self.email = email
		self.pec = pec
		self.phone = phone

		self.address = address or None
		self.cap = cap or None
		self.city = city or None
		self.full_address = mount_full_address(address, cap, city) or None

		self.vat_number = vat_number
		self.fiscal_code = fiscal_code
		self.sdi_code = sdi_code or None

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
		Partner.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		return {
			'id': self.id,
			'organization': self.organization,

			'client': self.client,
			'supplier': self.supplier,
			'partner': self.partner,

			'email': self.email,
			'pec': self.pec,
			'phone': self.phone,

			'address': self.address,
			'cap': self.cap,
			'city': self.city,
			'full_address': mount_full_address(self.address, self.cap, self.city),

			'vat_number': self.vat_number,
			'fiscal_code': self.fiscal_code,
			'sdi_code': self.sdi_code,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
