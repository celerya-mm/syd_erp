from datetime import datetime

from config import db
from app.functions import date_to_str

# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa


class Item(db.Model):
	# Table
	__tablename__ = 'items'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	item_code = db.Column(db.String(8), index=True, unique=True, nullable=False)
	item_code_supplier = db.Column(db.String(25), index=True, unique=False, nullable=True)

	item_description = db.Column(db.String(500), index=True, unique=False, nullable=False)

	item_price = db.Column(db.Float, index=False, unique=False, nullable=False)
	item_price_discount = db.Column(db.Float, index=False, unique=False, nullable=True)  # considerato in %
	item_currency = db.Column(db.String(3), index=False, unique=False, nullable=True)

	item_quantity_min = db.Column(db.Float, index=False, unique=False, nullable=True)  # min unità di acquisto
	item_quantity_um = db.Column(db.String(25), index=False, unique=False, nullable=True)

	supplier_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)
	supplier_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)

	supplier = db.relationship('Partner', backref='s_items', viewonly=True)
	supplier_site = db.relationship('PartnerSite', backref='ss_items', viewonly=True)

	oda_rows = db.relationship('OdaRow', backref='items', viewonly=True, lazy='dynamic')

	events = db.relationship('EventDB', backref='items', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<ITEM_CLASS: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ITEM_CLASS: [{self.item_code}] - {self.item_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Item.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		return {
			'id': self.id,

			'item_code': self.item_code,
			'item_code_supplier': self.item_code_supplier,
			'item_description': self.item_description,

			'item_price': self.item_price,
			'item_price_discount': self.item_price_discount,
			'item_currency': self.item_currency,

			'item_quantity_min': self.item_quantity_min,
			'item_quantity_um': self.item_quantity_um,

			'supplier_id': self.supplier_id,
			'supplier_site_id': self.supplier_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
