from datetime import datetime

from app.app import db


# Define the Role data-model
class Role(db.Model):
    # Table
    __tablename__ = 'roles'
    # Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), index=True, unique=True, nullable=False)

    user_roles = db.relationship('User', secondary='user_roles', backref='u_roles', lazy='dynamic')

    created_at = db.Column(db.DateTime, index=False, nullable=False)
    updated_at = db.Column(db.DateTime, index=False, nullable=False)

    def __repr__(self):
        return f'<RUOLO: {self.name}>'

    def __str__(self):
        return f'<RUOLO: {self.name}>'

    def __init__(self, name):
        self.name = name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def create(self):
        """Crea un nuovo record e lo salva nel db."""
        db.session.add(self)
        db.session.commit()

    def update(_id, data):  # noqa
        """Salva le modifiche a un record."""
        Role.query.filter_by(id=_id).update(data)
        db.session.commit()

    def to_dict(self):
        """Esporta in un dict la classe."""
        from app.functions import date_to_str
        return {
            'id': self.id,
            'name': self.name,
            'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
            'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f"),
        }


# Define the UserRoles association table
class UserRoles(db.Model):
    # Table
    __tablename__ = 'user_roles'
    # Columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=True)

    created_at = db.Column(db.DateTime, index=False, nullable=False)
    updated_at = db.Column(db.DateTime, index=False, nullable=False)

    def __repr__(self):
        return f'<RUOLO: {self.role_id} - UTENTE: {self.user_id}>'

    def __str__(self):
        return f'<RUOLO: {self.role_id} - UTENTE: {self.user_id}>'

    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def create(self):
        """Crea un nuovo record e lo salva nel db."""
        db.session.add(self)
        db.session.commit()

    def update():  # noqa
        """Salva le modifiche a un record."""
        db.session.commit()

    def remove(self):
        """Cancella un record."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Esporta in un dict la classe."""
        from app.functions import date_to_str

        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'created_at': date_to_str(self.created_at, "%Y-%m-%d %H:%M:%S.%f"),
            'updated_at': date_to_str(self.updated_at, "%Y-%m-%d %H:%M:%S.%f"),
        }
