from datetime import datetime, date

import pandas as pd


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
