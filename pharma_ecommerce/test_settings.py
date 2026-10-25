"""Isolated test settings: no production database, storage, Redis or email."""
import os
import atexit
import shutil
import tempfile

os.environ.setdefault("SECRET_KEY", "isolated-tests-only-never-use-in-production")
os.environ["USE_MINIO"] = "false"

from .settings import *  # noqa: F403

DEBUG = False
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
HEALTHCHECK_STORAGE = False
MEDIA_ROOT = tempfile.mkdtemp(prefix="lifeline-test-uploads-")
atexit.register(shutil.rmtree, MEDIA_ROOT, ignore_errors=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "ERROR"},
}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
