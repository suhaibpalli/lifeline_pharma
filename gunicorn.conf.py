"""Bounded production workers; shared by systemd and optional Docker backend."""
import os

bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "sync"
timeout = 60
graceful_timeout = 30
keepalive = 5
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "500"))
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = "info"
access_log_format = '%(h)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s duration=%(L)s'
