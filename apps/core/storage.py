"""Keep patient/profile documents private while catalogue assets stay public."""
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.functional import cached_property
from storages.backends.s3 import S3Storage


class PrivateMediaStorage(S3Storage):
    def get_default_settings(self):
        defaults = super().get_default_settings()
        defaults.update(
            custom_domain=None,
            querystring_auth=True,
            querystring_expire=300,
            default_acl="private",
            object_parameters={"CacheControl": "private, no-store"},
        )
        return defaults

    @cached_property
    def public_signer(self):
        # Upload/download operations use the internal endpoint. Signing needs
        # the browser-facing hostname, which nginx forwards unchanged to MinIO.
        return S3Storage(
            endpoint_url=settings.MINIO_PUBLIC_ENDPOINT_URL,
            bucket_name=self.bucket_name,
            custom_domain=None,
            querystring_auth=True,
            querystring_expire=300,
            access_key=self.access_key,
            secret_key=self.secret_key,
            region_name=self.region_name,
            signature_version="s3v4",
            addressing_style="path",
        )

    def url(self, name, parameters=None, expire=None, http_method=None):
        return self.public_signer.url(name, parameters, expire, http_method)


def get_private_storage():
    if settings.USE_MINIO:
        return PrivateMediaStorage()
    return FileSystemStorage()
