from datetime import timedelta, date
from app.app import db

# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa
from app.organizations.partners.models import Partner  # noqa
from app.organizations.partner_sites.models import PartnerSite  # noqa
from app.invoices.invoice_rows.models import InvoiceRow  # noqa


class Invoice(db.Model):
	# Table
	__tablename__ = 'invoices'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	invoice_number = db.Column(db.String(8), index=True, unique=True, nullable=False)
	invoice_date = db.Column(db.Date, index=False, unique=False, nullable=False)
	invoice_year = db.Column(db.Integer, index=True, unique=False, nullable=True)

	invoice_description = db.Column(db.String(255), index=False, unique=False, nullable=False)
	invoice_category = db.Column(db.String(50), index=True, unique=False, nullable=False)

	invoice_amount = db.Column(db.Numeric(10, 2), index=False, unique=False, nullable=True, default=None)
	invoice_currency = db.Column(db.String(3), index=False, unique=False, nullable=False)
	invoice_payment = db.Column(db.String(50), index=False, unique=False, nullable=False)
	invoice_status = db.Column(db.String(25), index=False, unique=False, nullable=False)

	invoice_expiration_date = db.Column(db.Date, index=False, unique=False, nullable=True)
	invoice_expired = db.Column(db.Boolean, index=True, unique=False, nullable=True)

	invoice_pdf = db.Column(db.LargeBinary, index=False, nullable=True)

	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id'), nullable=True)

	client_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
	client_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id'), nullable=True)

	client_order_nr = db.Column(db.String(25), index=False, unique=False, nullable=True)
	client_order_date = db.Column(db.Date, index=False, unique=False, nullable=True)

	plant = db.relationship('Plant', backref='p_invoices', viewonly=True)
	plant_site = db.relationship('PlantSite', backref='ps_invoices', viewonly=True)

	client = db.relationship('Partner', backref='c_invoices', viewonly=True)
	client_site = db.relationship('PartnerSite', backref='cs_invoices', viewonly=True)

	invoice_rows = db.relationship('InvoiceRow', backref='invoices', lazy='dynamic')

	events = db.relationship('EventDB', backref='invoices', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<INVOICE_CLASS: [{self.invoice_number}] - {self.invoice_description}>'

	def __str__(self):
		return f'<INVOICE_CLASS: [{self.invoice_number}] - {self.invoice_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Invoice.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		if self.invoice_payment:
			# calcola l'ultimo giorno del mese della data di fattura
			fine_mese = (self.invoice_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

			if '30' in self.invoice_payment:
				expiration = fine_mese + timedelta(days=30)
			elif '60' in self.invoice_payment:
				expiration = fine_mese + timedelta(days=60)
			elif '90' in self.invoice_payment:
				expiration = fine_mese + timedelta(days=90)
			else:
				expiration = self.invoice_date
		else:
			expiration = None

		if expiration not in [None, '']:
			if self.invoice_status not in ['Pagata_OK', 'Pagata_Ritardo']:
				expired = bool(expiration < date.today())
			else:
				expired = False
		else:
			expired = False

		return {
			'id': self.id,

			'invoice_number': self.invoice_number,
			'invoice_date': date_to_str(self.invoice_date, "%Y-%m-%d"),
			'invoice_year': self.invoice_date.year,

			'invoice_description': self.invoice_description,
			'invoice_category': self.invoice_category,

			'invoice_amount': self.invoice_amount,
			'invoice_currency': self.invoice_currency,
			'invoice_payment': self.invoice_payment,
			'invoice_status': self.invoice_status,

			'invoice_expiration_date': date_to_str(expiration),
			'invoice_expired': expired,

			'invoice_pdf': self.invoice_pdf,

			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id or None,

			'client_order_nr': self.client_order_nr,
			'client_order_date': date_to_str(self.client_order_date, "%Y-%m-%d"),

			'client_id': self.client_id,
			'client_site_id': self.client_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
