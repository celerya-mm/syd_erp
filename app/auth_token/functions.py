from .models import AuthToken


def __save_auth_token(token, user_id=None):
	"""Salvo il token nel DB."""
	try:
		auth_token = AuthToken(user_id=user_id, token=token)
		AuthToken.create(auth_token)
		return True
	except Exception as err:
		return err
