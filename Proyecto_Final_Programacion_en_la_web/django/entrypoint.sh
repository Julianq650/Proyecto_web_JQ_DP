#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
# Crea el administrador la primera vez; si ya existe, sigue sin error
python manage.py createsuperuser --noinput || true
# Usuarios y reservas de ejemplo (solo la primera vez)
if [ "$CARGAR_DEMO" = "1" ]; then python manage.py cargar_demo; fi
exec gunicorn djangobase.wsgi:application --bind 0.0.0.0:8000 --workers 2 --log-level warning --error-logfile -
