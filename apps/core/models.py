from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Base model with created and updated timestamps"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteConfiguration(TimeStampedModel):
    """Site-wide configuration settings"""

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class ContactInquiry(TimeStampedModel):
    """Contact form submissions"""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_inquiries",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class DeliveryZone(TimeStampedModel):
    """Delivery zones and charges"""

    name = models.CharField(max_length=100)
    pincode_start = models.CharField(max_length=6)
    pincode_end = models.CharField(max_length=6)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2)
    is_serviceable = models.BooleanField(default=True)
    estimated_days = models.PositiveIntegerField(default=2)

    class Meta:
        verbose_name = "Delivery Zone"
        verbose_name_plural = "Delivery Zones"

    def __str__(self):
        return f"{self.name} ({self.pincode_start}-{self.pincode_end})"


class Page(TimeStampedModel):
    """Static pages like About, Privacy Policy, etc."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"

    def __str__(self):
        return self.title


def carousel_upload_to(instance, filename):
    """Generate upload path for carousel images"""
    ext = filename.split(".")[-1]
    return f"carousel/{instance.id or 'new'}/{filename}"


# Lazy storage - resolves at runtime when USE_MINIO is available
def get_default_storage():
    from django.conf import settings

    if hasattr(settings, "USE_MINIO") and settings.USE_MINIO:
        from storages.backends.s3boto3 import S3Boto3Storage

        bucket_name = getattr(settings, "AWS_S3_STORAGE_BUCKET_NAME", None) or getattr(
            settings, "MINIO_BUCKET_NAME", "lifeline-media"
        )
        return S3Boto3Storage(bucket_name=bucket_name)
    from django.core.files.storage import FileSystemStorage

    return FileSystemStorage()


class CarouselImage(TimeStampedModel):
    """Carousel images for homepage"""

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(
        upload_to=carousel_upload_to,
        storage=get_default_storage(),
        null=True,
        blank=True,
        help_text="Upload carousel image",
    )
    button_text = models.CharField(max_length=50, default="Learn More")
    button_link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Relative or absolute URL (e.g., /products/ or https://lifelinehealthcare.in/products/)",
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Carousel Image"
        verbose_name_plural = "Carousel Images"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title
