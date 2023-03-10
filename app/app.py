import os
import secrets  # noqa

from flask import Flask, session  # noqa
from flask_caching import Cache
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

# imposto la cache per l'app (simple_cache, time_out=3600s)
cache = Cache(app)

# secret key
app.secret_key = Config.SECRET_KEY

# imposta invio mail
mail = Mail(app)

# formattazione avanzata del testo
Misaka(app)

# imposta sessione browser per server gunicorn
Session(app)

# impostazioni DB
db.init_app(app)

migrate = Migrate(app, db)
migrate.init_app(app, db)

# importo i Blueprint
with app.app_context():
	from app.event_db.routes import event_bp

	from app.organizations.plant.routes import plant_bp
	from app.organizations.plant_site.routes import plant_site_bp

	from app.account.routes import account_bp
	from app.roles.routes import role_bp

	from app.orders.order.routes import oda_bp
	from app.orders.order_rows.routes import oda_rows_bp
	from app.orders.items.routes import item_bp

	from app.organizations.partner_contacts.routes import partner_contact_bp
	from app.organizations.partner_sites.routes import partner_site_bp
	from app.organizations.partners.routes import partner_bp

	from app.invoices.activities.routes import activity_bp
	from app.invoices.invoice.routes import invoice_bp
	from app.invoices.invoice_rows.routes import invoice_rows_bp

	from app.business.opportunities.routes import opportunity_bp

	# registro i blueprints
	app.register_blueprint(event_bp, url_prefix='/event')

	app.register_blueprint(plant_bp, url_prefix='/plant')
	app.register_blueprint(plant_site_bp, url_prefix='/plant/site')

	app.register_blueprint(account_bp, url_prefix='/account')
	app.register_blueprint(role_bp, url_prefix='/role')

	app.register_blueprint(oda_bp, url_prefix='/oda')
	app.register_blueprint(oda_rows_bp, url_prefix='/oda_row')
	app.register_blueprint(item_bp, url_prefix='/item')

	app.register_blueprint(partner_contact_bp, url_prefix='/partner/contact')
	app.register_blueprint(partner_site_bp, url_prefix='/partner/site')
	app.register_blueprint(partner_bp, url_prefix='/partner')

	app.register_blueprint(activity_bp, url_prefix='/activity')
	app.register_blueprint(invoice_bp, url_prefix='/invoice')
	app.register_blueprint(invoice_rows_bp, url_prefix='/invoice_row')

	app.register_blueprint(opportunity_bp, url_prefix='/opportunity')
