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
