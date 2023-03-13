from datetime import date
from app.app import db

# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa
from app.organizations.partners.models import Partner  # noqa
from app.organizations.partner_sites.models import PartnerSite  # noqa


class Opportunity(db.Model):
	# Table
	__tablename__ = 'opportunities'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	opp_activity = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
	opp_value = db.Column(db.Numeric(10, 2), index=False, unique=False, nullable=True)

	opp_date = db.Column(db.Date, index=False, unique=False, nullable=False)
	opp_year = db.Column(db.Integer, index=True, unique=False, nullable=True)

	opp_description = db.Column(db.String(500), index=False, unique=False, nullable=False)
	opp_category = db.Column(db.String(50), index=True, unique=False, nullable=False)

	opp_status = db.Column(db.String(25), index=True, unique=False, nullable=False)

	opp_time_spent = db.Column(db.Numeric(3, 1), index=False, unique=False, nullable=True)

	opp_expiration_date = db.Column(db.Date, index=False, unique=False, nullable=True)
	opp_expired = db.Column(db.Boolean, index=True, unique=False, nullable=True)

	opp_accountable = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id'), nullable=True)

	partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
	partner_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id'), nullable=True)
	partner_contact_id = db.Column(db.Integer, db.ForeignKey('partner_contacts.id'), nullable=False)

	plant = db.relationship('Plant', backref='p_opportunities', viewonly=True)
	plant_site = db.relationship('PlantSite', backref='ps_opportunities', viewonly=True)
	
	accountable = db.relationship('User', backref='acc_opportunities', viewonly=True)
	activity = db.relationship('Activity', backref='act_opportunities', viewonly=True)
	
	partner = db.relationship('Partner', backref='p_opportunities', viewonly=True)
	partner_site = db.relationship('PartnerSite', backref='ps_opportunities', viewonly=True)
	partner_contact = db.relationship('PartnerContact', backref='pc_opportunities', viewonly=True)

	actions = db.relationship('Action', backref='opportunities', lazy='dynamic')

	events = db.relationship('EventDB', backref='opportunities', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<OPPORTUNITY_CLASS: [{self.id}] - {self.opp_description}>'

	def __str__(self):
		return f'<OPPORTUNITY_CLASS: [{self.id}] - {self.opp_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Opportunity.query.filter_by(id=_id).update(data)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str

		if self.opp_expiration_date not in [None, '']:
			if 'closed' not in self.opp_status.lower():
				expired = bool(self.opp_expiration_date < date.today())
			else:
				expired = False
		else:
			expired = False

		return {
			'id': self.id,
			'opp_activity': self.opp_activity,
			'opp_value': self.opp_value or None,

			'opp_date': date_to_str(self.opp_date, "%Y-%m-%d"),
			'opp_year': self.opp_date.year,

			'opp_description': self.opp_description,
			'opp_category': self.opp_category,

			'opp_status': self.opp_status,
			'opp_time_spent': self.opp_time_spent,

			'opp_expiration_date': date_to_str(self.opp_expiration_date),
			'opp_expired': expired,

			'opp_accountable': self.opp_accountable,

			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id or None,

			'partner_id': self.partner_id,
			'partner_site_id': self.partner_site_id or None,
			'partner_contact_id': self.partner_contact_id or None,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
