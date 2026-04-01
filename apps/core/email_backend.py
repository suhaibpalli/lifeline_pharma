import ssl

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend


class ConfigurableSMTPEmailBackend(EmailBackend):
    """SMTP backend with optional certificate verification bypass."""

    @property
    def ssl_context(self):
        if getattr(settings, "EMAIL_VALIDATE_CERTS", True):
            return ssl.create_default_context()

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
