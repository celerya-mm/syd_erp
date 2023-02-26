""""
	Al primo accesso, o secondo necessità, crea l'utente 'superuser' e gli assegna il relativo ruolo 'superuser'.

	Inoltre, crea i privilegi di accesso (Ruoli) per ogni tabella presente nel DB secondo la regola:
		<nome_tabella>_<ruolo>.
	I Ruoli sono compresi nella lista: admin, create, write e delete.

	Verificare bene, che i campi presenti nelle Classi User, Role e UserRole corrispondano a quelli configurati
	all'interno della app.
"""

import hashlib
from datetime import datetime

from config import Config
from sqlalchemy import create_engine, inspect, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
inspector = inspect(engine)


Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
	# Table
	__tablename__ = 'users'
	# Columns
	id = Column(Integer, primary_key=True, autoincrement=True)
	username = Column(String(20), index=True, unique=True, nullable=False)

	password = Column(String(64), index=False, unique=False, nullable=False)  # 64 char for hash code
	psw_changed = Column(Boolean, unique=False, nullable=False)

	active = Column(Boolean, unique=False, nullable=False)

	name = Column(String(50), index=False, unique=False, nullable=True)
	last_name = Column(String(50), index=False, unique=False, nullable=True)
	full_name = Column(String(101), index=False, unique=True, nullable=True)

	email = Column(String(80), index=False, unique=True, nullable=True)
	phone = Column(String(25), index=False, unique=False, nullable=True)

	address = Column(String(150), index=False, unique=False, nullable=True)
	cap = Column(String(5), index=False, unique=False, nullable=True)
	city = Column(String(55), index=False, unique=False, nullable=True)
	full_address = Column(String(255), index=False, unique=False, nullable=True)

	roles = relationship('Role', secondary='user_roles', backref='roles_user', lazy='dynamic', viewonly=True)

	note = Column(String(255), index=False, unique=False, nullable=True)

	created_at = Column(DateTime, index=False, nullable=False)
	updated_at = Column(DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<USER: [{self.id}] - {self.username}>'

	def __str__(self):
		return f'<USER: [{self.id}] - {self.username}>'

	def __init__(self, username, password, psw_changed, active, name, last_name, phone, email, address, cap, city, note):

		self.username = username

		self.password = password
		self.psw_changed = psw_changed

		self.active = active

		self.name = name
		self.last_name = last_name
		self.full_name = f'{name} {last_name}'

		self.phone = phone
		self.email = email

		self.address = address
		self.cap = cap
		self.city = city
		self.full_address = f'{address} - {cap} - {city}'

		self.note = note or None
		self.created_at = datetime.now()
		self.updated_at = datetime.now()


class Role(Base):
	# Table
	__tablename__ = 'roles'
	# Columns
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(50), index=True, unique=True, nullable=False)

	user_roles = relationship('User', secondary='user_roles', backref='users_role', lazy='dynamic')

	created_at = Column(DateTime, index=False, nullable=False)
	updated_at = Column(DateTime, index=False, nullable=False)

	def __repr__(self):
		return '<RUOLO: {}>'.format(self.name)

	def __str__(self):
		return '<RUOLO: {}>'.format(self.name)

	def __init__(self, name):
		self.name = name
		self.created_at = datetime.now()
		self.updated_at = datetime.now()


class UserRoles(Base):
	# Table
	__tablename__ = 'user_roles'
	# Columns
	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer(), ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
	role_id = Column(Integer(), ForeignKey('roles.id', ondelete='CASCADE'), nullable=True)

	created_at = Column(DateTime, index=False, nullable=False)
	updated_at = Column(DateTime, index=False, nullable=False)

	def __repr__(self):
		return f'<RUOLO: {self.role_id} - UTENTE: {self.user_id}>'

	def __str__(self):
		return f'<RUOLO: {self.role_id} - UTENTE: {self.user_id}>'

	def __init__(self, user_id, role_id):
		self.user_id = user_id
		self.role_id = role_id
		self.created_at = datetime.now()
		self.updated_at = datetime.now()


def create_superuser():
	""""Crea superuser"""
	_users = session.query(User).filter_by(username='celerya_superuser').first()
	if _users is None:
		new_user = User(
			username='celerya_superuser',
			password=hashlib.sha256('SuperUser_01'.encode('utf-8')).hexdigest(),
			psw_changed=False,
			active=True,
			name='Marco',
			last_name=None,
			email='develop@celerya.com',
			phone='+39 391 735 3416',
			address='Via Don Turinetti, 11',
			cap='10080',
			city='Bosconero (TO)',
			note=None
		)
		session.add(new_user)
		session.commit()
		print('Superuser CREATO')
		return True
	else:
		print('Superuser PRESENTE')
		return False


def create_superuser_role():
	roles = session.query(Role).all()
	if roles and [_r.name == 'superuser' for _r in roles]:
		print('RUOLO superuser PRESENTE.')
		return True
	else:
		pass

	new_role = Role(name='superuser')
	session.add(new_role)
	session.commit()
	print('RUOLO superuser CREATO.')
	return True


def assign_superuser_role():
	_user = session.query(User).filter_by(username='celerya_superuser').first()
	u_id = _user.id

	_role = session.query(Role).filter_by(name='superuser').first()
	r_id = _role.id

	role_assigned = session.query(UserRoles).filter_by(user_id=u_id, role_id=r_id).first()

	if role_assigned is None:
		user_role = UserRoles(user_id=u_id, role_id=r_id)
		session.add(user_role)
		session.commit()
		print('RUOLO superuser ASSEGNATO a UTENTE superuser.')
	else:
		print("RUOLO superuser a UTENTE superuser GIA' ASSEGNATO.")

	return True


def create_tables_roles():
	""""Crea i ruoli per ogni tabella presente nel DB (admin, read, write, delete)."""
	roles = session.query(Role).all()
	_list_roles = []
	if roles:
		for role in roles:
			if role not in _list_roles:
				_list_roles.append(role.name)

	_list_name = ['admin', 'read', 'write', 'delete']
	table_names = inspector.get_table_names()
	for table in table_names:
		for name in _list_name:
			name = f'{table}_{name}'
			if table in ['alembic_version', ]:
				pass
			elif name not in _list_roles:
				new_role = Role(name=name)
				session.add(new_role)
				session.commit()
				print(f'RUOLO {name} CREATO correttamente.')
			else:
				print(f'RUOLO {name} già PRESENTE.')


create_superuser()
create_superuser_role()
assign_superuser_role()
create_tables_roles()
