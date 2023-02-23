from datetime import datetime, timedelta

from app.functions import timer_func
from .models import AuthToken


@timer_func
def __save_auth_token(token, user_id=None):
	"""Salvo il token nel DB."""
	try:
		_time = datetime.now()
		_expires = (_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

		auth_token = AuthToken(
			user_id=user_id,
			token=token,
			created_at=_time,
			expires_at=_expires,
		)
		AuthToken.create(auth_token)
		return True
	except Exception as err:
		return err
