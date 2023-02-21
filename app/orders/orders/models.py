from datetime import datetime

from config import db
from app.functions import date_to_str

# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa
from app.organizations.partners.models import Partner  # noqa
from app.organizations.partner_sites.models import PartnerSite  # noqa


class Oda(db.Model):
	# Table
	__tablename__ = 'orders'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	oda_number = db.Column(db.String(8), index=True, unique=True, nullable=False)
	oda_date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
	oda_description = db.Column(db.String(80), index=False, unique=False, nullable=False)
	oda_delivery_date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
	oda_amount = db.Column(db.Float, index=False, unique=False, nullable=True)
	oda_currency = db.Column(db.String(3), index=False, unique=False, nullable=False)
	oda_payment = db.Column(db.String(50), index=False, unique=False, nullable=False)
	oda_status = db.Column(db.String(25), index=False, unique=False, nullable=False)

	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id'), nullable=True)
	plant = db.relationship('Plant', backref='p_orders', viewonly=True)
	plant_site = db.relationship('PlantSite', backref='ps_orders', viewonly=True)

	supplier_offer = db.Column(db.String(20), index=True, unique=True, nullable=True)
	supplier_offer_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)
	supplier_invoice = db.Column(db.String(20), index=True, unique=True, nullable=True)
	supplier_invoice_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)

	supplier_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
	supplier_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id'), nullable=True)
	supplier = db.relationship('Partner', backref='s_orders', viewonly=True)
	supplier_site = db.relationship('PartnerSite', backref='ss_orders', viewonly=True)

	events = db.relationship('EventDB', backref='orders', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<ODA_CLASS: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ODA_CLASS: [{self.item_code}] - {self.item_description}>'

	def __init__(self, oda_number, oda_date, oda_description, oda_delivery_date, oda_amount, oda_currency, oda_payment,
				 oda_status, plant_id, plant_site_id, supplier_offer, supplier_offer_date, supplier_invoice,
				 supplier_invoice_date, supplier_id, supplier_site_id, note):

		self.oda_number = oda_number
		self.oda_date = oda_date
		self.oda_description = oda_description
		self.oda_delivery_date = oda_delivery_date
		self.oda_amount = oda_amount
		self.oda_currency = oda_currency
		self.oda_payment = oda_payment
		self.oda_status = oda_status

		self.plant_id = plant_id
		self.plant_site_id = plant_site_id

		self.supplier_offer = supplier_offer
		self.supplier_offer_date = supplier_offer_date
		self.supplier_invoice = supplier_invoice
		self.supplier_invoice_date = supplier_invoice_date

		self.supplier_id = supplier_id
		self.supplier_site_id = supplier_site_id

		self.note = note or None
		self.created_at = datetime.now()
		self.updated_at = datetime.now()

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Oda.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		return {
			'id': self.id,

			'oda_number': self.oda_number,
			'oda_date': self.oda_date,
			'oda_description': self.oda_description,
			'oda_delivery_date': self.oda_delivery_date,
			'oda_amount': self.oda_amount,
			'oda_currency': self.oda_currency,
			'oda_payment': self.oda_payment,
			'oda_status': self.oda_status,

			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id or None,

			'supplier_offer': self.supplier_offer,
			'supplier_offer_date': self.supplier_offer_date,
			'supplier_invoice': self.supplier_invoice,
			'supplier_invoice_date': self.supplier_invoice_date,

			'supplier_id': self.supplier_id,
			'supplier_site_id': self.supplier_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
