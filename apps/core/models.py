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
class RetailerEnquiry(TimeStampedModel):
    ORDER_VALUE_CHOICES = [
        ('<50k', 'Less than 50,000'),
        ('50k-1L', '50,000 - 1 Lakh'),
        ('1L-5L', '1 Lakh - 5 Lakhs'),
        ('5L+', 'More than 5 Lakhs'),
    ]
    
    business_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    gst_number = models.CharField(max_length=20, blank=True)
    estimated_order_value = models.CharField(max_length=20, choices=ORDER_VALUE_CHOICES)
    message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Retailer Enquiry"
        verbose_name_plural = "Retailer Enquiries"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.business_name} - {self.contact_person}"


class ProductCatalogue(TimeStampedModel):
    title = models.CharField(max_length=200, default="Product Catalogue")
    description = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='catalogues/')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Product Catalogue"
        verbose_name_plural = "Product Catalogues"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class DoctorVisitRequest(TimeStampedModel):
    SPECIALIZATION_CHOICES = [
        ('General Physician', 'General Physician'),
        ('Cardiologist', 'Cardiologist'),
        ('Dermatologist', 'Dermatologist'),
        ('Pediatrician', 'Pediatrician'),
        ('Orthopedic', 'Orthopedic'),
        ('Gynecologist', 'Gynecologist'),
        ('ENT Specialist', 'ENT Specialist'),
        ('Neurologist', 'Neurologist'),
        ('Psychiatrist', 'Psychiatrist'),
        ('Ophthalmologist', 'Ophthalmologist'),
        ('Other', 'Other'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('Morning', 'Morning (9:00 AM - 12:00 PM)'),
        ('Afternoon', 'Afternoon (12:00 PM - 3:00 PM)'),
        ('Evening', 'Evening (3:00 PM - 6:00 PM)'),
    ]
    
    doctor_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    hospital_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    purpose = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Doctor Visit Request"
        verbose_name_plural = "Doctor Visit Requests"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Dr. {self.doctor_name} - {self.preferred_date}"
