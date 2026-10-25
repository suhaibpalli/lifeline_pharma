#!/bin/bash
set -e

echo ">>> Waiting for PostgreSQL..."
until python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_ecommerce.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('PostgreSQL ready.')
" 2>/dev/null; do
  echo "    PostgreSQL not ready yet — retrying in 2s..."
  sleep 2
done

echo ">>> Running migrations..."
python manage.py migrate --noinput

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo ">>> Starting Gunicorn..."
exec gunicorn --config gunicorn.conf.py pharma_ecommerce.wsgi:application
