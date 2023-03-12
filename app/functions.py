from datetime import datetime, date
from functools import wraps
from time import time

from flask import url_for, redirect
from sqlalchemy import Null

from .app import session


def token_user_validate(func):
	"""Eseguo la funzione solo se presente token autenticazione admin valido."""
	from app.auth_token.models import AuthToken
	from app.users.models import User
	from app.users.routes import B_PRINT

	@wraps(func)
	def wrap(*args, **kwargs):
		if session is not None and "token_login" in session.keys():
			# controlla validità token
			authenticated = AuthToken.query.filter_by(token=str(session["token_login"])).first()
			_user = User.query.get(authenticated.user_id)
			if authenticated is None:
				print("AUTHORIZATION_CHECK_FAIL token don't match.")
				msg = f"Non è stato passato un token valido, ripetere la login."
				return redirect(url_for(f'{B_PRINT}.logout', msg=msg))
			elif authenticated.expires_at < datetime.now():
				print("AUTHORIZATION_CHECK_FAIL token_expired:", authenticated.expires_at)
				msg = f"Il token è scaduto: {authenticated.expires_at}, ripetere la login."
				return redirect(url_for(f'{B_PRINT}.logout', msg=msg))
			elif authenticated.user_id in ["", None]:
				print("AUTHORIZATION_CHECK_FAIL user don't match.")
				msg = f"Non è registrato nessun utente con username '{session['user']['username']}', " \
					  f"provare a ripetere la login."
				return redirect(url_for(f'{B_PRINT}.logout', msg=msg))
			elif _user.active is False:
				print("AUTHORIZATION_CHECK_FAIL user_active:", _user.active)
				msg = f"L'utente {_user.username} non è abilitato all'accesso."
				return redirect(url_for(f'{B_PRINT}.logout', msg=msg))
			else:
				# esegue la funzione
				return func(*args, **kwargs)
		else:
			print("AUTHORIZATION_CHECK_FAIL_1")
			msg = f'Per accedere devi prima effettuare la login.'
			return redirect(url_for(f'{B_PRINT}.logout', msg=msg))

	return wrap


def access_required(roles='ANY'):
	"""Verifica se l'utente ha la regola assegnata per accedere."""

	def wrapper(fn):
		@wraps(fn)
		def check_rule(roles_=roles, *args, **kwargs):
			if session['user']['psw_changed'] is not True:
				from app.users.routes import B_PRINT, TABLE
				msg = 'Per poter proseguire devi aggiornare la tua password.'
				redirect(url_for(f"{B_PRINT}.{TABLE}_update_password", _id=session['user']['id'], msg=msg))
			elif 'user_roles' not in session.keys() or roles_ == 'ANY':
				msg = "Non hai i permessi per accedere alla risorsa richiesta."
				return msg
			else:
				for r in session['user_roles']:
					if r in roles_ or r == 'superuser':
						print(f'CHECK_ROLE: {r} [ OK ]')
						return fn(*args, **kwargs)

				# print(f"RUOLI: {session['user_roles']}")
				msg = f"Non hai i permessi per accedere alla risorsa richiesta. Contatta l'amministratore " \
					  f"per farti assegnare il permesso d'accesso."
				return msg

		return check_rule

	return wrapper


def access_required_update_psw(roles='ANY'):
	"""Verifica se l'utente ha il permesso per accedere."""

	def wrapper(fn):
		@wraps(fn)
		def check_rule(roles_=roles, *args, **kwargs):
			if session['user']['psw_changed'] is not True:
				return fn(*args, **kwargs)
			elif 'user_roles' not in session.keys() or roles_ == 'ANY':
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


def timer_func(fn):
	"""Calcola il tempo di esecuzione di una funzione."""

	@wraps(fn)
	def wrapper(*args, **kwargs):
		t1 = time()
		# chiama la funzione
		result = fn(*args, **kwargs)
		print(f'Function {fn.__name__!r} executed in {(time() - t1):.4f}s')
		# ritorna il risultato della funzione
		return result

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
	if _date in [None, "None", "nan", ""]:
		return None
	elif isinstance(_date, date):
		return date.strftime(_date, _form)
	elif isinstance(_date, datetime):
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
		return _v


def status_true_false(_stat):
	"""Cambia valori SI, NO in True, False."""
	if _stat in ['SI', 'si', True, 'True', 'y', 'Y', 1]:
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


def serialize_dict(obj):
	"""Verifica presenza campi data e li converte in iso format."""
	if isinstance(obj, datetime):
		return obj.isoformat()
	elif isinstance(obj, date):
		return obj.isoformat()
	else:
		raise TypeError(f"{obj} is not JSON serializable")
