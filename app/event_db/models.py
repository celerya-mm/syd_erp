from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from config import db


class EventDB(db.Model):
    # Table
    __tablename__ = 'events_db'
    # Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(JSONB, index=True, unique=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, index=False, nullable=False)

    def __repr__(self):
        return '<EVENTO: {}>'.format(self.event)

    def __str__(self):
        return '<EVENTO: {}>'.format(self.event)

    def __init__(self, event, user_id=None):
        self.event = event

        self.user_id = user_id

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

            'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
        }
