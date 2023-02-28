import base64
import os
from datetime import datetime, date

import qrcode
import pandas as pd

from app.app import PATH_PROJECT as _path

# imposta path qrcode
folder_temp_qrcode = os.path.join(_path, "static", "qrcode_temp")
if not os.path.exists(folder_temp_qrcode):
	os.makedirs(folder_temp_qrcode)

# imposta path temp file
folder_temp_pdf = os.path.join(_path, "orders", "orders", "temp_pdf")
if not os.path.exists(folder_temp_pdf):
	os.makedirs(folder_temp_pdf)


def generate_qr_code(_str, nr_cert):
	"""Genera un QR-Code da una stringa."""
	try:
		nr_cert = nr_cert.replace("/", "_") + ".jpg"

		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_Q,
			box_size=15,
			border=1,
		)
		qr.add_data(_str)
		qr.make(fit=True)

		img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
		img.save(os.path.join(folder_temp_qrcode, nr_cert))

		return nr_cert
	except Exception as err:
		print(err)
		return False


def byte_to_pdf(byte, f_name):
	"""Ricrea il pdf da una stringa in byte."""
	# svuoto la cartella da file vecchio
	for filename in os.listdir(folder_temp_pdf):
		file_path = os.path.join(folder_temp_pdf, filename)
		os.remove(file_path)

	path_file = os.path.join(folder_temp_pdf, f_name.replace("/", "_") + ".pdf")

	with open(path_file, "wb") as f:
		f.write(byte)
	return path_file


def pdf_to_byte(_pdf):
	"""Converte pdf in byte string."""
	try:
		with open(_pdf, "rb") as f:
			b_string = str(base64.b64encode(f.read()), 'utf-8')
			b_string = base64.b64decode(b_string)
		os.remove(_pdf)
		return b_string
	except FileNotFoundError as err:
		print(err)
		return False


def dict_group_by(_dict, group_d, group_f=None, amount=None, year=False):  # group_d deve essere l'anno se year=True
	"""Raggruppa un DF per la richiesta passata (group)."""
	# crea DF
	df = pd.DataFrame.from_records(_dict)

	if year:
		# filtra DF al massimo cinque anni indietro
		past_year = datetime.now().year - 5
		for i, row in df.iterrows():
			if isinstance(row[group_d], str) or isinstance(row[group_d], datetime) or isinstance(row[group_d], date):
				_date = pd.to_datetime(row[group_d])
				df.at[i, group_d] = int(_date.year)
			elif isinstance(row[group_d], int):
				pass
			else:
				print('ERRORE CAMPO ANNO:', row[group_d], type(row[group_d]))

		df = df.loc[df[group_d] >= past_year]

	# raggruppa il DF
	if group_f and amount:
		df = df.groupby(by=group_f)[amount].sum().reset_index()
		df = df.sort_values(by=[group_f])
		dct = df.to_dict("records")
	elif group_f:
		df = df.groupby([group_d, group_f]).size().reset_index()
		df.rename(columns={0: 'number'}, inplace=True)
		df = df.sort_values(by=[group_f])
		dct = df.to_dict("records")
	elif amount:
		df = df.groupby(group_d)[amount].sum().reset_index()
		df = df.sort_values(by=[group_d])
		dct = df.to_dict("records")
	else:
		df = df.groupby(by=group_d).size().reset_index()
		df.rename(columns={0: 'number'}, inplace=True)
		print(df)
		dct = df.to_dict("records")
	return dct
