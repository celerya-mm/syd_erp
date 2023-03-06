# import json
import simplejson as json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.app import session, db, PATH_PROJECT as _path
from app.functions import token_user_validate, access_required, timer_func
from .functions import dict_group_by

from .forms import FormOda
from .models import Oda

oda_bp = Blueprint(
	'oda_bp', __name__,
	template_folder='templates',
	static_folder='static'
)

VIEW = "/view/"
VIEW_FOR = "oda_bp.oda_view"
VIEW_HTML = "oda_view.html"

CREATE = "/create/<int:p_id>/<int:s_id>/"
CREATE_FOR = "oda_bp.oda_create"
CREATE_HTML = "oda_create.html"

DETAIL = "/view/detail/<int:_id>"
DETAIL_FOR = "oda_bp.oda_view_detail"
DETAIL_HTML = "oda_view_detail.html"

UPDATE = "/update/<int:_id>"
UPDATE_FOR = "oda_bp.oda_update"
UPDATE_HTML = "oda_update.html"

GENERATE = "/generate/<int:_id>"
GENERATE_FOR = "oda_bp.oda_generate"

DOWNLOAD = "/download/<int:_id>/"
DOWNLOAD_FOR = "oda_bp.oda_download"


@oda_bp.route(VIEW, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_read'])
def oda_view():
	"""Visualizzo informazioni ODA."""
	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as SITE_DETAIL

	# Estraggo la lista dei partners
	_list = Oda.query.all()
	_list = [r.to_dict() for r in _list]

	# raggruppo per anno ordine (5 anni max)
	g_year = dict_group_by(_list, 'oda_date', amount='oda_amount', year=True)
	y_labels = [sub['oda_date'] for sub in g_year]
	y_values = [sub['oda_amount'] for sub in g_year]

	# raggruppa per fornitore
	g_supplier = dict_group_by(_list, 'oda_date', group_f="supplier_id", amount='oda_amount', year=True)
	s_labels = [sub["supplier_id"] for sub in g_supplier]
	s_values = [sub['oda_amount'] for sub in g_supplier]

	db.session.close()
	return render_template(VIEW_HTML, form=_list, create=CREATE_FOR, detail=DETAIL_FOR, partner_detail=PARTNER_DETAIL,
						   site_detail=SITE_DETAIL, y_labels=json.dumps(y_labels), y_values=json.dumps(y_values),
						   s_labels=json.dumps(s_labels), s_values=json.dumps(s_values))


@oda_bp.route(CREATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_write'])
def oda_create(p_id, s_id=None):
	"""Creazione ODA."""
	from app.organizations.plant.models import Plant

	from app.organizations.partners.models import Partner
	from app.organizations.partner_sites.models import PartnerSite

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	form = FormOda.new(spl_id=p_id)

	if request.method == 'POST' and form.validate():
		try:
			form_data = FormOda(request.form).to_dict()
			# print('NEW_CONTACT:', json.dumps(form_data, indent=2))

			new_oda = Oda(
				oda_number=form_data['oda_number'],
				oda_date=form_data['oda_date'],
				oda_description=form_data['oda_description'],
				oda_delivery_date=form_data['oda_delivery_date'],
				oda_currency=form_data['oda_currency'],
				oda_payment=form_data['oda_payment'],
				oda_status=form_data['oda_status'],

				plant_id=form_data["plant_id"],
				plant_site_id=form_data["plant_site_id"],

				supplier_offer=form_data["supplier_offer"],
				supplier_offer_date=form_data["supplier_offer_date"],
				supplier_invoice=form_data["supplier_invoice"],
				supplier_invoice_date=form_data["supplier_invoice_date"],

				supplier_id=form_data["supplier_id"],
				supplier_site_id=form_data["supplier_site_id"],

				note=form_data["note"],
				created_at=form_data["updated_at"],
				updated_at=form_data["updated_at"]
			)

			Oda.create(new_oda)
			flash("ODA creato correttamente.")

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
		# setto il nuovo numero d'ordine
		last_id = Oda.query.order_by(Oda.id.desc()).first()
		if last_id is None:
			form.oda_number.data = 'oda_0001'
		else:
			form.oda_number.data = f'oda_{str(int(last_id.oda_number.split("_")[1]) + 1).zfill(4)}'

		# Estraggo dati azienda
		plant = Plant.query.get(1)
		form.plant_id.data = f'{plant.id} - {plant.organization}'
		# print('PLANT:', form.plant_id.data)

		# Estraggo dati fornitore
		partner = Partner.query.get(p_id)
		form.supplier_id.data = f'{partner.id} - {partner.organization}'
		# print('PARTNER:', form.supplier_id.data)

		if s_id:
			partner_site = PartnerSite.query.get(s_id)
			form.supplier_site_id.data = f'{partner_site.id} - {partner_site.organization}'
			# print('PARTNER_SITE:', form.supplier_site_id.data)

		return render_template(
			CREATE_HTML, form=form,
			partner_view=PARTNER_DETAIL, p_id=p_id,
			partner_site_view=PARTNER_SITE_DETAIL, s_id=s_id,
		)


@oda_bp.route(DETAIL, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_read'])
def oda_view_detail(_id):
	"""Visualizzo il dettaglio del record."""
	from app.event_db.routes import DETAIL_FOR as EVENT_DETAIL

	from app.organizations.partners.routes import DETAIL_FOR as PARTNER_DETAIL
	from app.organizations.partner_sites.routes import DETAIL_FOR as PARTNER_SITE_DETAIL

	from app.orders.order_rows.routes import (CREATE_FOR as ODA_ROW_CREATE, DETAIL_FOR as ODA_ROW_DETAIL,
											  DELETE_FOR as ODA_ROW_DELETE)

	# Interrogo il DB
	oda = Oda.query \
		.options(joinedload(Oda.plant)) \
		.options(joinedload(Oda.plant_site)) \
		.options(joinedload(Oda.supplier)) \
		.options(joinedload(Oda.supplier_site)) \
		.get(_id)

	_oda = oda.to_dict()

	# Estraggo la storia delle modifiche per l'articolo
	history_list = oda.events
	if history_list:
		history_list = [history.to_dict() for history in history_list]
	else:
		history_list = []

	# Organizzazione
	_oda["plant_id"] = f'{oda.plant.id} - {oda.plant.organization}'

	if oda.plant_site:
		_oda["plant_site_id"] = f'{oda.plant_site.id} - {oda.plant_site.organization}'

	# Fornitore
	_oda["supplier_id"] = f'{oda.supplier.id} - {oda.supplier.organization}'
	p_id = oda.supplier.id

	if oda.supplier_site:
		_oda["supplier_site_id"] = f'{oda.supplier_site.id} - {oda.supplier_site.site}'
		s_id = oda.supplier_site.id
	else:
		s_id = None

	# Estraggo la lista delle righe ordine
	rows_list = oda.oda_rows
	if rows_list:
		rows_list = [row.to_dict() for row in rows_list]
	else:
		rows_list = []

	amount = oda.oda_amount
	if rows_list:
		_oda["oda_amount"] = 0
		for row in rows_list:
			_oda["oda_amount"] = round(_oda["oda_amount"] + row["item_amount"], 2)
	else:
		_oda["oda_amount"] = None

	if amount != _oda["oda_amount"]:
		oda.oda_amount = _oda["oda_amount"]
		Oda.update(_id, oda.to_dict())
		flash("TOTALE ORDINE aggiornato.")

		previous_data = oda.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "oda_pdf"]]
		previous_data['oda_amount'] = str(previous_data['oda_amount'])

		from app.event_db.routes import event_create
		_event = {
			"username": session["user"]["username"],
			"table": Oda.__tablename__,
			"Modification": f"Update ODA whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, order_id=_id)

	db.session.close()
	return render_template(
		DETAIL_HTML, form=_oda, view=VIEW_FOR, update=UPDATE_FOR, oda_generate=GENERATE_FOR, oda_download=DOWNLOAD_FOR,
		event_detail=EVENT_DETAIL, history_list=history_list, h_len=len(history_list),
		partner_detail=PARTNER_DETAIL, p_id=p_id,
		partner_site_detail=PARTNER_SITE_DETAIL, s_id=s_id,
		oda_row_create=ODA_ROW_CREATE, row_detail=ODA_ROW_DETAIL, row_delete=ODA_ROW_DELETE,
		rows_list=rows_list, r_len=len(rows_list),
	)


@oda_bp.route(UPDATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_write'])
def oda_update(_id):
	"""Aggiorna dati ODA."""
	from app.event_db.routes import event_create

	# recupero i dati
	oda = Oda.query \
		.options(joinedload(Oda.plant)) \
		.options(joinedload(Oda.plant_site)) \
		.options(joinedload(Oda.supplier)) \
		.options(joinedload(Oda.supplier_site)) \
		.get(_id)

	form = FormOda.update(obj=oda, pl_id=oda.plant_id, spl_id=oda.supplier_id)

	if request.method == 'POST' and form.validate():
		new_data = FormOda(request.form).to_dict()

		previous_data = oda.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "oda_pdf"]]
		previous_data['oda_amount'] = str(previous_data['oda_amount'])

		try:
			Oda.update(_id, new_data)
			flash("ODA aggiornato correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			_info = {
				'created_at': oda.created_at,
				'updated_at': oda.updated_at,
			}
			return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)

		_event = {
			"username": session["user"]["username"],
			"table": Oda.__tablename__,
			"Modification": f"Update ODA whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, order_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		# Organizzazione
		form.plant_id.data = f'{oda.plant.id} - {oda.plant.organization}'
		form.plant_site_id.data = f'{oda.plant_site.id} - {oda.plant_site.site}' if oda.plant_site else None

		# Fornitore
		form.supplier_id.data = f'{oda.supplier.id} - {oda.supplier.organization}'
		form.supplier_site_id.data = f'{oda.supplier_site.id} - {oda.supplier_site.site}' if oda.supplier_site else None

		_info = {
			'created_at': oda.created_at,
			'updated_at': oda.updated_at,
		}
		db.session.close()
		return render_template(UPDATE_HTML, form=form, id=_id, info=_info, history=DETAIL_FOR)


@oda_bp.route("/<form>/<form_rows>/", methods=["GET", "POST"])
@timer_func
@token_user_validate
def html_to_pdf(oda, oda_rows):  # , _qrcode):
	"""Genera pdf da template html."""
	import pdfkit
	import os
	from .functions import folder_temp_pdf  # , folder_temp_qrcode

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

		if oda.oda_currency == '€':
			oda.oda_currency = 'Euro'

		html = render_template('oda_to_pdf.html', oda=oda, oda_rows=oda_rows, logo=logo, sign=sign)  # , qrcode=_img)
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


@oda_bp.route(GENERATE, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_write'])
def oda_generate(_id):
	"""Genera il pdf di un ODA."""
	from app.orders.order_rows.models import OdaRow
	from .functions import pdf_to_byte
	from app.event_db.routes import event_create

	oda = Oda.query.options(joinedload(Oda.supplier)).get(_id)
	oda_row = OdaRow.query.filter_by(oda_id=_id).order_by(OdaRow.id.asc()).all()

	pdf = html_to_pdf(oda, oda_row)

	if pdf:
		pdf_byte = pdf_to_byte(pdf)
	else:
		db.session.close()
		flash(f"ERRORE CREAZIONE FILE PDF.")
		return redirect(url_for(DETAIL_FOR, _id=_id))

	if pdf_byte not in [False, None]:
		previous_data = oda.to_dict()
		[previous_data.pop(key) for key in ["updated_at", "oda_pdf"]]
		previous_data['oda_amount'] = str(previous_data['oda_amount'])

		# assegno stringa in byte
		oda.oda_pdf = pdf_byte
		oda.oda_status = 'Generato'
		if oda.oda_currency == 'Euro':
			oda.oda_currency = '€'

		try:
			Oda.update(_id, oda.to_dict())
			flash("ODA CREATO correttamente.")
		except IntegrityError as err:
			db.session.rollback()
			db.session.close()
			flash(f"ERRORE: {str(err.orig)}")
			return redirect(url_for(DETAIL_FOR, _id=_id))

		_event = {
			"username": session["user"]["username"],
			"table": Oda.__tablename__,
			"Modification": f"Update ODA whit id: {_id}",
			"Previous_data": previous_data
		}
		_event = event_create(_event, order_id=_id)
		return redirect(url_for(DETAIL_FOR, _id=_id))
	else:
		flash(f"ERRORE CREAZIONE BYTE PDF.")
		db.session.close()
		return redirect(url_for(DETAIL_FOR, _id=_id))


@oda_bp.route(DOWNLOAD, methods=["GET", "POST"])
@timer_func
@token_user_validate
@access_required(roles=['orders_admin', 'orders_read'])
def oda_download(_id):
	"""Genera file pdf da stringa in byte."""
	import os
	from flask import send_file
	from .functions import byte_to_pdf
	from PyPDF2 import PdfReader, PdfMerger

	oda = Oda.query.get(_id)
	db.session.close()
	if oda.oda_pdf and len(oda.oda_pdf) > 100:
		_pdf = byte_to_pdf(oda.oda_pdf, oda.oda_number)
		_payment_condition = os.path.join(_path, "orders", "order", "attachments", "CG_Celerya_Rev_12_2020.pdf")
		_merged = os.path.join(_path, "orders", "orders", "temp_pdf", "_merged.pdf")

		merger = PdfMerger()
		with open(_pdf, 'rb') as f:
			merger.append(PdfReader(f))

		with open(_payment_condition, 'rb') as f:
			merger.append(PdfReader(f))

		with open(_merged, 'wb') as f:
			merger.write(f)

		try:
			os.remove(_pdf)
			os.rename(_merged, _pdf)
		except Exception as err:
			print(f"Errore durante la generazione del pdf: {err}")
			msg = f"Errore durante la generazione del pdf: {err}"
			return msg

		return send_file(_pdf, as_attachment=True)
	else:
		flash("Errore generazione certificato. ")
		return redirect(url_for(DETAIL_FOR, _id=_id))
