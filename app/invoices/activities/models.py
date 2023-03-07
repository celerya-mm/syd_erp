from app.app import db


# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa


class Activity(db.Model):
	# Table
	__tablename__ = 'activities'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	activity_code = db.Column(db.String(8), index=True, unique=True, nullable=False)

	activity_description = db.Column(db.String(500), index=True, unique=False, nullable=False)

	activity_price = db.Column(db.Numeric(10, 2), index=False, unique=False, nullable=True)
	activity_currency = db.Column(db.String(3), index=False, unique=False, nullable=True)

	activity_quantity = db.Column(db.Float, index=False, unique=False, nullable=True)  # min unità di acquisto
	activity_quantity_um = db.Column(db.String(25), index=False, unique=False, nullable=True)

	activity_estimated_time = db.Column(db.Float, index=False, unique=False, nullable=True)

	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id', ondelete='CASCADE'), nullable=True)

	plant = db.relationship('Plant', backref='p_activities', viewonly=True)
	plant_site = db.relationship('PlantSite', backref='ps_activities', viewonly=True)
	# invoice_rows = db.relationship('InvoiceRow', backref='activity', viewonly=True, lazy='dynamic')

	events = db.relationship('EventDB', backref='items', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<ACTIVITY_CLASS: [{self.activity_code}] - {self.activity_description}>'

	def __str__(self):
		return f'<ACTIVITY_CLASS: [{self.activity_code}] - {self.activity_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Activity.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		return {
			'id': self.id,

			'activity_code': self.activity_code,
			'activity_description': self.activity_description,

			'activity_price': self.activity_price,
			'activity_currency': self.activity_currency,

			'activity_quantity': self.activity_quantity,
			'activity_quantity_um': self.activity_quantity_um,

			'activity_estimated_time': self.activity_estimated_time,

			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
