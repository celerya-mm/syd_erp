# import json
from datetime import datetime

import simplejson as json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db, PATH_PROJECT as _path
from app.functions import token_user_validate, access_required, timer_func
from .functions import dict_group_by

from .forms import FormInvoice
from .models import Invoice

invoice_bp = Blueprint(
	'invoice_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

TABLE = Invoice.__tablename__
BLUE_PRINT, B_PRINT = invoice_bp, 'invoice_bp'

VIEW = "/view/"
VIEW_FOR = f"{B_PRINT}.{TABLE}_view"
VIEW_HTML = f"{TABLE}_view.html"

CREATE = "/create/<int:p_id>/<int:s_id>/"
CREATE_FOR = f"{B_PRINT}.{TABLE}_create"
CREATE_HTML = f"{TABLE}_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = f"{B_PRINT}.{TABLE}_view_detail"
DETAIL_HTML = f"{TABLE}_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = f"{B_PRINT}.{TABLE}_update"
UPDATE_HTML = f"{TABLE}_update.html"

GENERATE = "/generate/<int:_id>"
GENERATE_FOR = f"{B_PRINT}.{TABLE}_generate"

DOWNLOAD = "/download/<int:_id>/"
DOWNLOAD_FOR = f"{B_PRINT}.{TABLE}_download"


@BLUE_PRINT.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def invoices_view():
	"""Visualizzo informazioni ODA."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	if request.method == 'POST':
		year = request.form.get('year')
		print('YEAR:', year)
		if year:
			_list = Invoice.query.filter_by(invoice_year=year).all()
			if len(_list):
				flash(f"Ordini trovati: {len(_list)}")
			else:
				_list = Invoice.query.all()
				flash("Nessun Fattura emessa nel periodo cercato.")
				flash('Mostro tutti i records.')
		else:
			_list = Invoice.query.all()
			flash(f"Nessun Anno selezionato, mostro tutti i records: {len(_list)}")
	else:
		_list = Invoice.query.all()

	# Estraggo la lista delle fatture
	_list = [r.to_dict() for r in _list]

	if _list:
		# raggruppo per anno ordine (5 anni max)
		g_year = dict_group_by(_list, 'invoice_date', amount='invoice_amount', year=True)
		y_labels = [sub['invoice_date'] for sub in g_year]
		y_values = [sub['invoice_amount'] for sub in g_year]

		# raggruppa per fornitore
		g_supplier = dict_group_by(_list, 'invoice_date', group_f="client_id", amount='invoice_amount', year=True)
		s_labels = [sub["client_id"] for sub in g_supplier]
		s_values = [sub['invoice_amount'] for sub in g_supplier]

		# raggruppa per categoria
		g_category = dict_group_by(_list, 'invoice_date', group_f="invoice_category", amount='invoice_amount', year=True)
		c_labels = [sub["invoice_category"] for sub in g_category]
		c_values = [sub['invoice_amount'] for sub in g_category]
	else:
		y_labels, y_values, s_labels, s_values, c_labels, c_values = [], [], [], [], [], []

	db.session.close()
	return render_template(
		VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL,
		site_detail=SITE_DETAIL, y_labels=json.dumps(y_labels), y_values=json.dumps(y_values),
		s_labels=json.dumps(s_labels), s_values=json.dumps(s_values),
		c_labels=json.dumps(c_labels), c_values=json.dumps(c_values)
	)


@BLUE_PRINT.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def invoices_create(p_id, s_id=None):
	"""Creazione OFFERTA."""
	from app.organizations.plants.models import Plant

	from app.organizations.partners.models import Partner
	from app.organizations.partner_sites.models import PartnerSite

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	form = FormInvoice.new(spl_id=p_id)

	if request.method == 'POST' and form.validate():
		try:
			form_data = FormInvoice(request.form).to_dict()
			# print('NEW_CONTACT:', json.dumps(form_data, indent=2))

			_time = datetime.now()

			new_invoice = Invoice(
				invoice_number=form_data['invoice_number'],
				invoice_date=form_data['invoice_date'],

				invoice_description=form_data['invoice_description'],
				invoice_category=form_data['invoice_category'],

				invoice_currency=form_data['invoice_currency'],
				invoice_payment=form_data['invoice_payment'],
				invoice_status=form_data['invoice_status'],

				plant_id=form_data["plant_id"],
				plant_site_id=form_data["plant_site_id"],

				client_order_nr=form_data["client_order_nr"],
				client_order_date=form_data["client_order_date"],

				client_id=form_data["client_id"],
				client_site_id=form_data["client_site_id"],

				note=form_data["note"],
				created_at=_time,
				updated_at=_time
			)

			Invoice.create(new_invoice)
			flash("FATTURA creata correttamente.")

			if s_id not in [None, 0]:
				return redirect(url_for(PARTNER_SITE_DETAIL, _id=s_id))
			else:
				return redirect(url_for(PARTNER_DETAIL, _id=p_id))

		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return render_template(
				CREATE_HTML, form=form,
				partner_view=PARTNER_DETAIL, p_id=p_id,
				partner_site_view=PARTNER_SITE_DETAIL, s_id=s_id,
			)
	else:
		# setto il nuovo numero offerta
		last_id = Invoice.query.order_by(Invoice.id.desc()).first()
		if last_id is None:
			form.invoice_number.data = 'inv_0001'
		else:
			form.invoice_number.data = f'inv_{str(int(last_id.invoice_number.split("_")[1]) + 1).zfill(4)}'

		# Estraggo dati azienda
		plant = Plant.query.get(1)
		form.plant_id.data = f'{plant.id} - {plant.organization}'
		# print('PLANT:', form.plant_id.data)

		# Estraggo dati fornitore
		partner = Partner.query.get(p_id)
		form.client_id.data = f'{partner.id} - {partner.organization}'
		# print('PARTNER:', form.supplier_id.data)

		if s_id:
			partner_site = PartnerSite.query.get(s_id)
			form.client_site_id.data = f'{partner_site.id} - {partner_site.organization}'
			# print('PARTNER_SITE:', form.supplier_site_id.data)

		return render_template(
			CREATE_HTML, form=form,
			partner_view=PARTNER_DETAIL, p_id=p_id,
			partner_site_view=PARTNER_SITE_DETAIL, s_id=s_id,
		)


@BLUE_PRINT.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def invoices_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	from app.invoices.invoice_rows.routes import (CREATE_FOR as INVOICE_ROW_CREATE, DETAIL_FOR as INVOICE_ROW_DETAIL,
											      DELETE_FOR as INVOICE_ROW_DELETE)

	# Interrogo il DB
	invoice = Invoice.query \
		.options(joinedload(Invoice.plant)) \
		.options(joinedload(Invoice.plant_site)) \
		.options(joinedload(Invoice.client)) \
		.options(joinedload(Invoice.client_site)) \
		.get(_id)

	_invoice = invoice.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = invoice.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Organizzazione
	_invoice["plant_id"] = f'{invoice.plant.id} - {invoice.plant.organization}'

	if invoice.plant_site:
		_invoice["plant_site_id"] = f'{invoice.plant_site.id} - {invoice.plant_site.organization}'

	# Fornitore
	_invoice["client_id"] = f'{invoice.client.id} - {invoice.client.organization}'
	p_id = invoice.client.id

	if invoice.client_site:
		_invoice["client_site_id"] = f'{invoice.client_site.id} - {invoice.client_site.site}'
		s_id = invoice.client_site.id
	else:
		s_id = None

	# Estraggo la lista delle righe fattura
	rows_list = invoice.invoice_rows
	if rows_list:
		rows_list = [row.to_dict() for row in rows_list]
	else:
		rows_list = []

	# Calcolo totale
	amount = invoice.invoice_amount
	if rows_list:
		_invoice["invoice_amount"] = 0
		for row in rows_list:
			_invoice["invoice_amount"] = round(_invoice["invoice_amount"] + row["activity_amount"], 2)
	else:
		_invoice["invoice_amount"] = None

	if amount != _invoice["invoice_amount"]:
		invoice.invoice_amount = _invoice["invoice_amount"]
		Invoice.update(_id, invoice.to_dict())
		flash("TOTALE FATTURA aggiornato.")

		previous_data = invoice.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "invoice_pdf"]]
		previous_data['invoice_amount'] = str(previous_data['invoice_amount'])

		from app.event_db.routes import events_db_create
		_event = {
			"username": session["user"]["username"],
			"table": Invoice.__tablename__,
			"Modification": f"Update INVOICE whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, invoice_id=_id)

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_invoice, view=VIEW_FOR, update=UPDATE_FOR,
		invoice_generate=GENERATE_FOR, invoice_download=DOWNLOAD_FOR,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		partner_detail=PARTNER_DETAIL, p_id=p_id,
		partner_site_detail=PARTNER_SITE_DETAIL, s_id=s_id,
		invoice_row_create=INVOICE_ROW_CREATE, row_detail=INVOICE_ROW_DETAIL, row_delete=INVOICE_ROW_DELETE,
		rows_list=rows_list, r_len=len(rows_list),
	)


@BLUE_PRINT.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def invoices_update(_id):
	"""Aggiorna dati OFFERTA."""
	from app.event_db.routes import events_db_create

	# recupero i dati
	invoice = Invoice.query \
		.options(joinedload(Invoice.plant)) \
		.options(joinedload(Invoice.plant_site)) \
		.options(joinedload(Invoice.client)) \
		.options(joinedload(Invoice.client_site)) \
		.get(_id)

	form = FormInvoice.update(obj=invoice, pl_id=invoice.plant_id, spl_id=invoice.client_id)

	if request.method == 'POST' and form.validate():
		new_data = FormInvoice(request.form).to_dict()

		previous_data = invoice.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "invoice_pdf"]]
		previous_data['invoice_amount'] = str(previous_data['invoice_amount'])

		try:
			Invoice.update(_id, new_data)
			flash("FATTURA aggiornata correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': invoice.created_at,
				'updated_at': invoice.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Invoice.__tablename__,
			"Modification": f"Update INVOICE whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, invoice_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		# Organizzazione
		form.plant_id.data = f'{invoice.plant.id} - {invoice.plant.organization}'
		form.plant_site_id.data = f'{invoice.plant_site.id} - {invoice.plant_site.site}' if invoice.plant_site else None

		# Fornitore
		form.client_id.data = f'{invoice.client.id} - {invoice.client.organization}'
		form.client_site_id.data = f'{invoice.client_site.id} - {invoice.client_site.site}' if invoice.client_site else None

		_info = {
			'created_at': invoice.created_at,
			'updated_at': invoice.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)


@BLUE_PRINT.route("/<form>/<form_rows>/", methods=["GET", "POST"])
@timer_func
@token_user_validate
def html_to_pdf(invoice, invoice_rows):  # , _qrcode):
	"""Genera pdf da template html."""
	import pdfkit
	import os
	from app.functions_pdf import folder_temp_pdf  # , folder_temp_qrcode

	# _img = os.path.join(_path, "static", "qrcode_temp", _qrcode)
	logo = os.path.join(_path, "static", "Logo_colore.png")
	sign = os.path.join(_path, "static", "TimbroFirma.png")

	# PDF options
	options = {
		"orientation": "portrait",
		"page-size": "A4",
		"margin-top": "0.5cm",
		"margin-right": "0.5cm",
		"margin-bottom": "0.5cm",
		"margin-left": "0.5cm",
		"encoding": "ascii",
		"enable-local-file-access": "",
		"print-media-type": True
	}

	try:
		# Build PDF from HTML
		_file = os.path.join(folder_temp_pdf, "report.pdf")

		if invoice.invoice_currency == '€':
			invoice.invoice_currency = 'Euro'

		html = render_template('invoice_to_pdf.html', oda=invoice, oda_rows=invoice_rows, logo=logo,
							   sign=sign)  # , qrcode=_img)
		_html = os.path.join(folder_temp_pdf, "temp.html")

		db.session.close()

		with open(_html.encode('ascii'), 'w') as f:
			f.write(html)

		_pdf = pdfkit.from_file(_html, False, options=options)

		with open(_file, "wb") as f:
			f.write(_pdf)

		# rimuovo il qrcode
		# for f in os.listdir(folder_temp_qrcode):
		# 	_f = os.path.join(folder_temp_qrcode, f)
		# 	os.remove(_f)

		return _file
	except Exception as err:
		print("ERRORE_CREAZIONE_PDF_DA_HTML:", err)
		return False


@BLUE_PRINT.route(GENERATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_write'])
def invoices_generate(_id):
	"""Genera il pdf di un'OFFERTA."""
	from app.orders.order_rows.models import OdaRow
	from app.functions_pdf import pdf_to_byte
	from app.event_db.routes import events_db_create

	invoice = Invoice.query.options(joinedload(Invoice.client)).get(_id)
	invoice_rows = OdaRow.query.filter_by(oda_id=_id).order_by(OdaRow.id.asc()).all()

	pdf = html_to_pdf(invoice, invoice_rows)

	if pdf:
		pdf_byte = pdf_to_byte(pdf)
	else:
		db.session.close()
		flash(f"ERRORE CREAZIONE FILE PDF.")
		return redirect(url_for(DETAIL_FOR, _id=_id))

	if pdf_byte not in [False, None]:
		previous_data = invoice.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "invoice_pdf"]]
		previous_data['invoice_amount'] = str(previous_data['invoice_amount'])

		# assegno stringa in byte
		invoice.oda_pdf = pdf_byte
		invoice.oda_status = 'Generato'
		if invoice.oda_currency == 'Euro':
			invoice.oda_currency = '€'

		try:
			Invoice.update(_id, invoice.to_dict())
			flash("ODA CREATO correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return redirect(url_for(DETAIL_FOR, _id=_id))

		_event = {
			"username": session["user"]["username"],
			"table": Invoice.__tablename__,
			"Modification": f"Update INVOICE whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = events_db_create(_event, invoice_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		flash(f"ERRORE CREAZIONE BYTE PDF.")
		db.session.close()
		return redirect(url_for(DETAIL_FOR, _id=_id))


@BLUE_PRINT.route(DOWNLOAD, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=[f'{TABLE}_admin', f'{TABLE}_read'])
def invoices_download(_id):
	"""Genera file pdf da stringa in byte."""
	import os
	from flask import send_file
	from app.functions_pdf import byte_to_pdf

	invoice = Invoice.query.get(_id)
	db.session.close()
	if invoice.invoice_pdf and len(invoice.invoice_pdf) > 100:
		_pdf = byte_to_pdf(invoice.invoice_pdf, invoice.invoice_number)

		try:
			os.remove(_pdf)
		except Exception as err:
			msg = f"ERRORE durante la generazione del pdf: {err}"
			print(msg)
			return msg

		return send_file(_pdf, as_attachment=True)
	else:
		flash("ERRORE generazione FATTURA pdf. ")
		return redirect(url_for(DETAIL_FOR, _id=_id))
