#!/bin/sh
# echo Starting app...

# lanciare l'app Flask tramite la porta 5000, il docker potrà essere esposto con altra porta eg. 8000
gunicorn -w 4 --threads 4 --log-config gunicorn/gunicorn_logging.conf -b 0.0.0.0:5000 --reload wsgi:app
