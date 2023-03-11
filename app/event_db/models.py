from sqlalchemy.dialects.postgresql import JSONB

from app.app import db


class EventDB(db.Model):
    # Table
    __tablename__ = 'events_db'
    # Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(JSONB, index=True, unique=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='CASCADE'), nullable=True)
    partner_contact_id = db.Column(db.Integer, db.ForeignKey('partner_contacts.id', ondelete='CASCADE'), nullable=True)
    partner_site_id = db.Column(db.Integer, db.ForeignKey('partner_sites.id', ondelete='CASCADE'), nullable=True)

    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='CASCADE'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=True)
    oda_row_id = db.Column(db.Integer, db.ForeignKey('oda_rows.id', ondelete='CASCADE'), nullable=True)

    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=True)
    plant_site_id = db.Column(db.Integer, db.ForeignKey('plant_sites.id', ondelete='CASCADE'), nullable=True)

    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id', ondelete='CASCADE'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=True)
    invoice_row_id = db.Column(db.Integer, db.ForeignKey('invoice_rows.id', ondelete='CASCADE'), nullable=True)

    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=True)

    created_at = db.Column(db.DateTime, index=False, nullable=False)

    def __repr__(self):
        return f'<EVENTO_RECORD: [{self.event}]>'

    def __str__(self):
        return f'<EVENTO_RECORD: [{self.event}]>'

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
            'partner_contact_id': self.partner_contact_id,
            'partner_site_id': self.partner_site_id,

            'item_id': self.item_id,
            'order_id': self.order_id,
            'oda_row_id': self.oda_row_id,

            'plant_id': self.plant_id,
            'plant_site_id': self.plant_site_id,

            'activity_id': self.activity_id,
            'invoice_id': self.invoice_id,
            'invoice_row_id': self.invoice_row_id,

            'opportunity_id': self.opportunity_id,

            'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
        }
