from app.app import db


# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa


class InvoiceRow(db.Model):
	# Table
	__tablename__ = 'invoice_rows'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	activity_code = db.Column(db.String(8), db.ForeignKey('activities.activity_code'), index=True, unique=False,
							  nullable=False)
	activity_description = db.Column(db.String(500), index=True, unique=False, nullable=False)

	activity_price = db.Column(db.Numeric(10, 2), index=False, unique=False, nullable=True)
	activity_price_discount = db.Column(db.Float, index=False, unique=False, nullable=True)  # considerato in %
	activity_currency = db.Column(db.String(3), index=False, unique=False, nullable=True)

	activity_quantity = db.Column(db.Float, index=False, unique=False, nullable=True)
	activity_quantity_um = db.Column(db.String(25), index=False, unique=False, nullable=True)

	activity_amount = db.Column(db.Numeric(10, 2), index=False, unique=False, nullable=True)

	invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)

	client_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)
	client_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)

	client = db.relationship('Partner', backref='c_invoice_rows', viewonly=True)
	client_site = db.relationship('PartnerSite', backref='cs_invoice_rows', viewonly=True)

	events = db.relationship('EventDB', backref='invoice_rows', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<INVOICE_ROW_CLASS: [{self.activity_code}] - {self.activity_description}>'

	def __str__(self):
		return f'<INVOICE_ROW_CLASS: [{self.activity_code}] - {self.activity_description}>'

	def calculate_activity_amount(self):
		if self.activity_price and self.activity_quantity and self.activity_price_discount:
			activity_amount = (float(self.activity_price) * float(self.activity_quantity)) * (
					(100 - float(self.activity_price_discount)) / 100
			)
		elif self.activity_price and self.activity_quantity:
			activity_amount = (float(self.activity_price) * float(self.activity_quantity))
		else:
			activity_amount = 0

		self.activity_amount = activity_amount

	def update_activity_amount(self):
		if self["activity_price"] and self['activity_quantity'] and self['activity_price_discount']:
			activity_amount = (self["activity_price"] * self['activity_quantity']) * (
					(100 - self['activity_price_discount']) / 100
			)
		elif self["activity_price"] and self['activity_quantity']:
			activity_amount = (self["activity_price"] * self['activity_quantity'])
		else:
			activity_amount = 0

		self['activity_amount'] = activity_amount

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		self.calculate_activity_amount()
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		InvoiceRow.update_activity_amount(data)
		InvoiceRow.query.filter_by(id=_id).update(data)
		db.session.commit()

	def remove(_id):  # noqa
		"""Cancella un record per id."""
		x = InvoiceRow.query.filter_by(id=_id).first()
		db.session.remove(x)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str
		return {
			'id': self.id,

			'activity_code': self.activity_code,
			'activity_description': self.activity_description,

			'activity_price': self.activity_price,
			'activity_price_discount': self.activity_price_discount,
			'activity_currency': self.activity_currency,

			'activity_quantity': self.activity_quantity,
			'activity_quantity_um': self.activity_quantity_um,

			'activity_amount': self.activity_amount,

			'invoice_id': self.invoice_id,

			'client_id': self.client_id,
			'client_site_id': self.client_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
