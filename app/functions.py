from datetime import datetime, date
from functools import wraps

from flask import url_for, redirect, flash
from sqlalchemy import Null

from .app import session


def token_user_validate(func):
	"""Eseguo la funzione solo se presente token autenticazione admin valido."""
	from .auth_token.models import AuthToken
	from .account.models import User

	@wraps(func)
	def wrap(*args, **kwargs):
		if session is not None and "token_login" in session.keys():
			# controlla validità token
			authenticated = AuthToken.query.filter_by(token=str(session["token_login"])).first()
			_user = User.query.get(authenticated.user_id)
			if authenticated is None:
				flash(f"Non è stato passato un token valido, ripetere la login.")
				return redirect(url_for('account_bp.logout'))
			elif authenticated.expires_at < datetime.now():
				flash(f"Il token è scaduto, ripetere la login.")
				return redirect(url_for('account_bp.logout'))
			elif authenticated.user_id in ["", None]:
				flash(f"Non è stato registrato nessun utente, effettuare la login.")
				return redirect(url_for('account_bp.logout'))
			elif _user.active is False:
				flash(f"L'utente {_user.username} non è abilitato all'accesso.")
				return redirect(url_for('account_bp.logout'))
			else:
				print("AUTHORIZATION_CHECK_PASS")
				# esegue la funzione
				return func(*args, **kwargs)
		else:
			print("AUTHORIZATION_CHECK_FAIL_1")
			return redirect(url_for('account_bp.logout'))

	return wrap


def access_required(roles='ANY'):
	"""Verifica se l'utente ha la regola assegnata per accedere."""

	def wrapper(fn):
		@wraps(fn)
		def check_rule(roles_=roles, *args, **kwargs):
			if 'user_roles' not in session.keys() or roles_ == 'ANY':
				msg = "Non hai i permessi per accedere alla risorsa richiesta."
				return msg
			else:
				for r in session['user_roles']:
					if r in roles_ or r == 'superuser':
						print(f'CHECK_ROLE: {r} [OK]')
						return fn(*args, **kwargs)

				msg = f"Non hai i permessi per accedere alla risorsa richiesta. Contatta l'amministratore " \
					  f"per farti assegnare il permesso d'accesso."
				return msg

		return check_rule
	return wrapper


def str_to_date(_str, _form="%Y-%m-%d"):
	"""Converte una stringa in datetime."""
	if _str in [None, ""]:
		return None
	elif _str not in [None, "None", "nan", ""] and isinstance(_str, str):
		return datetime.strptime(_str, _form)
	else:
		return _str


def date_to_str(_date, _form="%Y-%m-%d"):
	"""Converte datetime in stringa."""
	if _date in [None, ""]:
		return None
	elif _date not in [None, "None", "nan", ""] and isinstance(_date, datetime) or isinstance(_date, date):
		return datetime.strftime(_date, _form)
	else:
		return _date


def mount_full_name(name, last_name):
	"""Monta il nome completo."""
	if name is not None and last_name is not None:
		full_name = f"{name} {last_name}"
	elif name is not None and last_name is None:
		full_name = name
	elif name is None and last_name is not None:
		full_name = last_name
	else:
		full_name = None
	return full_name


def mount_full_address(address, cap, city):
	"""Monta indirizzo completo."""
	if address and cap and city:
		full_address = f"{address} - {cap} - {city}"
	elif address and cap:
		full_address = f"{address} - {cap}"
	elif address and city:
		full_address = f"{address} - {city}"
	elif cap and city:
		full_address = f"{cap} - {city}"
	elif address:
		full_address = address
	elif city:
		full_address = city
	elif cap:
		full_address = cap
	else:
		full_address = None

	return full_address


def not_empty(_v):
	"""Verifica se il dato passato è vuoto o da non considerare."""
	if _v in ["", "-", None, 0] or _v is Null:
		return None
	else:
		_v = str(_v).strip()
		return _v


def status_true_false(_stat):
	"""Cambia valori SI, NO in True, False."""
	if _stat in ['SI', 'si', True, 'y', 'Y', 1]:
		return True
	else:
		return False


def status_si_no(_str):
	"""Verifica se il dato passato contiene True o False e li converte in SI o NO."""
	if _str in ["SI", "si", "NO", "no"]:
		return _str
	elif _str is True:
		return "SI"
	else:
		return "NO"
