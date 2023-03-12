import hashlib
from password_strength import PasswordPolicy


# definisco la policy per le password
PSW_POLICY = PasswordPolicy.from_names(
	length=8,  # min length: 8
	uppercase=1,  # need min. 1 uppercase letters
	numbers=1,  # need min. 1 digits
	special=1,  # need min. 1 special
)


def psw_verify(password):
	verify_password = PSW_POLICY.test(password)
	if len(verify_password) > 0:
		data = {
			"01_status": "failed",
			"02_message": f"The password is too weak",
			"length": "8 characters minimum",
			"uppercase": "1 uppercase character minimum",
			"numbers": "1 digit minimum",
			"special_characters": "1 special character minimum"
		}
		return data
	else:
		return False


def psw_contain_usr(password, username):
	"""Controllo se la password è troppo simile allo username."""
	# converto in lower case
	user = str(username).lower()
	psw = str(password).lower()
	# tolgo primo e ultimo carattere da username
	user_1 = user[:-1]
	user_2 = user[1:]
	if user in psw:
		data = {
			'01_status': 'failed',
			'02_message': f'The password contain the username. Please chose another password.',
			'username': username,
			'password': password
		}
		return data
	elif user_1 in psw or user_2 in psw:
		if len(password) - len(username) <= 2:
			data = {
				"01_status": "failed",
				"02_message": "The password is too similar to the username. Please chose another password.",
				"username": username,
				"password": password
			}
			return data
		else:
			return False
	else:
		return False


def psw_hash(_psw):
	return hashlib.sha256(str(_psw).encode('utf-8')).hexdigest()
