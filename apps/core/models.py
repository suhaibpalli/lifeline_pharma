from django.db import models
# from django.contrib.auth.models import User
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
        related_name='resolved_inquiries'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"
        ordering = ['-created_at']
    
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

# apps/core/models.py
from django.db import models
# ... other imports ...

class CarouselImage(TimeStampedModel):
    """Carousel images for homepage"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)

    # NEW: accept an upload in admin / forms
    image_upload = models.ImageField(
        upload_to='carousel_uploads/',
        null=True,
        blank=True,
        help_text='Upload source image (will be converted to base64)'
    )

    # Keep base64 storage for runtime usage
    image_data = models.TextField(blank=True)  # Base64 encoded image
    button_text = models.CharField(max_length=50, default="Learn More")
    button_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Carousel Image"
        verbose_name_plural = "Carousel Images"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def save_image_as_base64(self, image_file):
        """Convert uploaded image to base64"""
        import base64
        from PIL import Image
        from io import BytesIO

        img = Image.open(image_file)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        img.thumbnail((1920, 800), Image.Resampling.LANCZOS)

        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85, optimize=True)
        img_io.seek(0)

        image_data = base64.b64encode(img_io.read()).decode('utf-8')
        self.image_data = image_data

    def save(self, *args, **kwargs):
        """
        If an image_upload file was provided, convert it to base64 and
        store in `image_data`. Optionally remove the uploaded file from storage.
        """
        if self.image_upload:
            try:
                # convert uploaded file to base64
                self.save_image_as_base64(self.image_upload)
            except Exception:
                # don't block saving; but you may want to log the error
                pass

            # Optional: remove the uploaded file from storage (clean up),
            # and set field to None so file won't be kept
            try:
                storage = self.image_upload.storage
                storage.delete(self.image_upload.name)
            except Exception:
                pass

            self.image_upload = None

        super().save(*args, **kwargs)
