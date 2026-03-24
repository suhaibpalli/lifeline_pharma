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
exec gunicorn pharma_ecommerce.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --log-level "${GUNICORN_LOG_LEVEL:-info}"
