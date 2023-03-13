from app.app import db


# importazioni per creare relazioni in tabella
from app.event_db.models import EventDB  # noqa


class Action(db.Model):
	# Table
	__tablename__ = 'actions'
	# Columns
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)

	action_description = db.Column(db.String(500), index=False, unique=False, nullable=False)
	action_category = db.Column(db.String(50), index=True, unique=False, nullable=False)
	
	action_date = db.Column(db.Date, index=False, unique=False, nullable=False)
	
	user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
	user = db.relationship('User', backref='p_actions', viewonly=True)

	action_time_spent = db.Column(db.Numeric(3, 1), index=False, unique=False, nullable=False)

	opp_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False)
	
	plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
	plant = db.relationship('Plant', backref='pl_actions', viewonly=True)
	
	plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id', ondelete='CASCADE'), nullable=True)
	plant_site = db.relationship('PlantSite', backref='pls_actions', viewonly=True)

	partner_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False)
	partner = db.relationship('Partner', backref='p_actions', viewonly=True)
	
	partner_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)
	partner_site = db.relationship('PartnerSite', backref='ps_actions', viewonly=True)
	
	partner_contact_id = db.Column(db.Integer, db.ForeignKey('partner_contacts.id', ondelete='CASCADE'), nullable=False)
	partner_contact = db.relationship('PartnerContact', backref='pc_actions', viewonly=True)

	events = db.relationship('EventDB', backref='actions', order_by='EventDB.id.desc()', lazy='dynamic')

	note = db.Column(db.String(255), index=False, unique=False, nullable=True)

	created_at = db.Column(db.DateTime, index=False, nullable=False)
	updated_at = db.Column(db.DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<ACTION_CLASS: [{self.id}] - {self.action_description}>'

	def __str__(self):
		return f'<ACTION_CLASS: [{self.id}] - {self.action_description}>'

	def create(self):
		"""Crea un nuovo record e lo salva nel db."""
		db.session.add(self)
		db.session.commit()

	def update(_id, data):  # noqa
		"""Salva le modifiche a un record."""
		Action.query.filter_by(id=_id).update(data)
		db.session.commit()

	def remove(_id):  # noqa
		"""Cancella un record per id."""
		x = Action.query.filter_by(id=_id).first()
		db.session.delete(x)
		db.session.commit()

	def to_dict(self):
		"""Esporta in un dict la classe."""
		from app.functions import date_to_str
		return {
			'id': self.id,

			'action_description': self.action_description,
			'action_category': self.action_category,
			
			'action_date': date_to_str(self.action_date),
			
			'user_id': self.user_id,

			'action_time_spent': self.action_time_spent,

			'opp_id': self.opp_id,
			
			'plant_id': self.plant_id,
			'plant_site_id': self.plant_site_id or None,

			'partner_id': self.partner_id,
			'partner_site_id': self.partner_site_id or None,
			'partner_contact_id': self.partner_contact_id,

			'note': self.note,
			'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
			'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f")
		}
