import os
import secrets  # noqa

from flask import Flask, session  # noqa
from flask_mail import Mail, Message  # noqa
from flask_migrate import Migrate
from flask_misaka import Misaka
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config, db

PATH_PROJECT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, instance_relative_config=False)

# imposto app dietro reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# carico parametri configurazione
app.config.from_object(Config)

# secret = secrets.token_urlsafe(32)
app.secret_key = Config.SECRET_KEY

# imposta invio mail
mail = Mail(app)

# formattazione avanzata del testo
Misaka(app)

# imposta sessione browser per server gunicorn
Session(app)

# impostazioni DB
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)


# importo i Blueprint
with app.app_context():
	from .account.routes import account_bp
	from .event_db.routes import event_bp
	from .roles.routes import role_bp

	from app.organizations.partners.routes import partner_bp
	from .organizations.contacts.routes import contact_bp

	# registro i blueprints
	app.register_blueprint(account_bp, url_prefix='/account')
	app.register_blueprint(event_bp, url_prefix='/event')
	app.register_blueprint(role_bp, url_prefix='/role')

	app.register_blueprint(partner_bp, url_prefix='/partner')
	app.register_blueprint(contact_bp, url_prefix='/partner/contact')
