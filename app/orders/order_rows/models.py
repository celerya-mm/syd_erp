from app.app import db


# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa


class OdaRow(db.Model):
	# Table
	__tablename__ = 'oda_rows'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	item_code = db.Column(
		db.String(8), db.ForeignKey('items.item_code', ondelete='CASCADE'), index=True, unique=False, nullable=False)
	item_code_supplier = db.Column(db.String(25), index=True, unique=False, nullable=True)
	item_description = db.Column(db.String(500), index=True, unique=False, nullable=False)

	item_price = db.Column(db.Float, index=False, unique=False, nullable=False)
	item_price_discount = db.Column(db.Float, index=False, unique=False, nullable=True)  # considerato in %
	item_currency = db.Column(db.String(3), index=False, unique=False, nullable=True)

	item_quantity = db.Column(db.Float, index=False, unique=False, nullable=True)
	item_quantity_um = db.Column(db.String(25), index=False, unique=False, nullable=True)

	item_amount = db.Column(db.Float, index=False, unique=False, nullable=True)

	oda_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)

	supplier_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)
	supplier_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)

	supplier = db.relationship('Partner', backref='s_oda_rows', viewonly=True)
	supplier_site = db.relationship('PartnerSite', backref='ss_oda_rows', viewonly=True)

	events = db.relationship('EventDB', backref='oda_rows', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<ORDER_ROW_CLASS: [{self.item_code}] - {self.item_description}>'

	def __str__(self):
		return f'<ORDER_ROW_CLASS: [{self.item_code}] - {self.item_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		OdaRow.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str
		return {
			'id': self.id,

			'item_code': self.item_code,
			'item_code_supplier': self.item_code_supplier,
			'item_description': self.item_description,

			'item_price': self.item_price,
			'item_price_discount': self.item_price_discount,
			'item_currency': self.item_currency,

			'item_quantity': self.item_quantity,
			'item_quantity_um': self.item_quantity_um,

			'item_amount': self.item_amount,
			'oda_id': self.oda_id,

			'supplier_id': self.supplier_id,
			'supplier_site_id': self.supplier_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
