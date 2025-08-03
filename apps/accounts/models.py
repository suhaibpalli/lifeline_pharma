from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from apps.core.models import TimeStampedModel
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    """Custom user model with email as username field"""
    
    USER_TYPE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('PHARMACY', 'Pharmacy'),
        ('ADMIN', 'Admin'),
    ]
    
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='PATIENT')
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_profile(self):
        """Get user profile based on user type"""
        if self.user_type == 'PATIENT':
            return getattr(self, 'patient_profile', None)
        elif self.user_type == 'PHARMACY':
            return getattr(self, 'pharmacy_profile', None)
        return None

class PatientProfile(TimeStampedModel):
    """Profile model for patients"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    medical_conditions = models.JSONField(default=list, blank=True)  # List of conditions
    allergies = models.JSONField(default=list, blank=True)  # List of allergies
    current_medications = models.JSONField(default=list, blank=True)  # List of current meds
    profile_image = models.TextField(blank=True)  # Base64 encoded image
    
    class Meta:
        verbose_name = _('Patient Profile')
        verbose_name_plural = _('Patient Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Patient"

class PharmacyProfile(TimeStampedModel):
    """Profile model for pharmacies"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='pharmacy_profile')
    business_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    gst_number = models.CharField(max_length=15, blank=True)
    business_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    license_document = models.TextField(blank=True)  # Base64 encoded document
    gst_certificate = models.TextField(blank=True)  # Base64 encoded document
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_pharmacies'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _('Pharmacy Profile')
        verbose_name_plural = _('Pharmacy Profiles')
    
    def __str__(self):
        return f"{self.business_name}"
    
    @property
    def available_credit(self):
        return self.credit_limit - self.credit_used

class Address(TimeStampedModel):
    """Address model for users"""
    
    ADDRESS_TYPE_CHOICES = [
        ('HOME', 'Home'),
        ('OFFICE', 'Office'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='HOME')
    name = models.CharField(max_length=100)  # Address label
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class EmailVerification(TimeStampedModel):
    """Email verification model"""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = _('Email Verification')
        verbose_name_plural = _('Email Verifications')
    
    def __str__(self):
        return f"Verification for {self.user.email}"
