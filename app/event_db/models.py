from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from config import db


class EventDB(db.Model):
    # Table
    __tablename__ = 'events_db'
    # Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(JSONB, index=True, unique=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=True)

    created_at = db.Column(db.DateTime, index=False, nullable=False)

    def __repr__(self):
        return f'<EVENTO: [{self.event}]>'

    def __str__(self):
        return f'<EVENTO: [{self.event}]>'

    def __init__(self, event, user_id=None, partner_id=None, contact_id=None):
        self.event = event

        self.user_id = user_id
        self.partner_id = partner_id
        self.contact_id = contact_id

        self.created_at = datetime.now()

    def create(self):
        """Crea un nuovo record e lo salva nel db."""
        db.session.add(self)
        db.session.commit()

    def update():  # noqa
        """Salva le modifiche a un record."""
        db.session.commit()

    def to_dict(self):
        """Esporta in un dict la classe."""
        from app.functions import date_to_str
        return {
            'id': self.id,
            'event': self.event,

            'user_id': self.user_id,
            'partner_id': self.partner_id,
            'contact_id': self.contact_id,

            'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
        }
