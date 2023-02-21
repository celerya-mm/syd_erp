import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()


class Config:
	"""Parametri configurazione."""
	ENV = os.getenv('FLASK_ENV', 'development')
	FLASK_DEBUG = os.getenv('FLASK_DEBUG', 1)
	SECRET_KEY = os.getenv('APP_SECRET_KEY', 'dev')
	BASE_URL = os.getenv('APP_BASE_URL', '127.0.0.1')
	LINK_URL = os.getenv('APP_URL_LINK')
	LINK_PORT = os.getenv('APP_URL_PORT')

	CACHE_TYPE = os.getenv('CACHE_TYPE')
	CACHE_DEFAULT_TIMEOUT = os.getenv('CACHE_DEFAULT_TIMEOUT')

	SESSION_PERMANENT = os.getenv('SESSION_PERMANENT')
	SESSION_TYPE = os.getenv('SESSION_TYPE')
	SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE')
	REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE')
	SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY')
	REMEMBER_COOKIE_HTTPONLY = os.getenv('REMEMBER_COOKIE_HTTPONLY')

	COMPOSE_IGNORE_ORPHANS = os.getenv('COMPOSE_IGNORE_ORPHANS')

	# setup smtp server
	MAIL_SERVER = os.getenv('MAIL_SERVER')
	MAIL_PORT = os.getenv('MAIL_PORT')
	MAIL_USERNAME = os.getenv('MAIL_USERNAME')
	MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
	MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
	MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')

	# setup DB
	SSQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
	SQLALCHEMY_DATABASE_URI = 'postgresql://{username}:{password}@{host}:{port}/{db_name}'.format(
		username=os.getenv('DB_USERNAME'),
		password=os.getenv('DB_PASSWORD'),
		host=os.getenv('DB_HOST', 'DB_HOST_OUT'),
		port=os.getenv('DB_PORT'),
		db_name=os.getenv('DB_NAME')
	)
