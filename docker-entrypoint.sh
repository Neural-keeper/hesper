#!/bin/sh
set -eu

.venv/bin/python manage.py migrate --noinput

exec "$@"
