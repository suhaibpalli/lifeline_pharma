# Agent Guidelines for Lifeline Healthcare Project

## Project Overview

Django 5.2.4 e-commerce platform for pharmacy/healthcare in India (INR currency).

### Key Features
- Custom user authentication (email-based, no username field)
- Multiple user types: PATIENT, PHARMACY, ADMIN
- Product catalog with prescription management (OTC/RX)
- Tiered pricing (MRP, Patient Price, Pharmacy Price)
- Order processing and tracking
- Shopping cart with wishlist support
- Delivery zone management by pincode
- Contact inquiry system
- Static pages (About, FAQ, Privacy Policy, Terms of Service)

### Company Details
- **Name**: Lifeline Healthcare
- **Address**: No.18/24, Ground Floor, Sri Ayyappa Nagar 2nd Main road, Virugambakkam, Chennai-600092
- **Email**: abijith.apollo@gmail.com
- **Phone**: 044 - 48633074 / 6381411751 / 9884433074

---

## Build/Test/Lint Commands

### Development Server
```bash
python manage.py runserver
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test apps.accounts
python manage.py test apps.products
python manage.py test apps.orders
python manage.py test apps.cart
python manage.py test apps.core

# Run a specific test class
python manage.py test apps.accounts.tests.CustomUserTestCase

# Run a specific test method
python manage.py test apps.accounts.tests.CustomUserTestCase.test_user_creation

# Run with verbosity
python manage.py test -v 2
```

### Django Management Commands
```bash
# Create superuser
python manage.py createsuperuser

# Seed site configuration
python manage.py seed_site_config

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check
python manage.py check --deploy
```

### Pre-commit Checklist
Before committing, run:
```bash
python manage.py check
python manage.py test
```

---

## Code Style Guidelines

### Python Style
- Follow PEP 8 with 4-space indentation
- Maximum line length: 120 characters
- Use type hints where beneficial
- Use `django.utils.translation.gettext_lazy as _` for verbose names
- Use triple quotes for docstrings

### Imports Order
```python
# Standard library
import uuid
from decimal import Decimal
from datetime import timedelta

# Django core
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

# Third party / external
from django.utils.text import slugify

# Local imports (within apps)
from apps.core.models import TimeStampedModel
from .models import CustomUser
```

---

## Models (apps/*/models.py)

### Base Model Pattern
All models inherit from `TimeStampedModel` for automatic `created_at`/`updated_at`:
```python
from apps.core.models import TimeStampedModel

class Example(TimeStampedModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
    ]
    
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    class Meta:
        verbose_name = _('Example')
        verbose_name_plural = _('Examples')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_pending(self):
        return self.status == 'PENDING'
```

### Key Patterns
- **CHOICES**: Define as class-level constants with uppercase keys
- **ForeignKey fields**: Always use `related_name` for reverse lookups
- **Base64 images**: Store as `TextField` (e.g., `profile_image`, `image_data`)
- **JSON fields**: Use for lists/dicts (e.g., `medical_conditions = JSONField(default=list)`)
- **Slug generation**: Override `save()` method with `slugify()`
- **Boolean defaults**: Use `blank=True` carefully; prefer explicit defaults

### Image Upload Pattern
```python
class CarouselImage(TimeStampedModel):
    image_upload = models.ImageField(upload_to='carousel_uploads/', null=True, blank=True)
    image_data = models.TextField(blank=True)  # Base64 storage
    
    def save(self, *args, **kwargs):
        if self.image_upload:
            # Convert to base64 and clean up upload
            self.save_image_as_base64(self.image_upload)
            self.image_upload = None
        super().save(*args, **kwargs)
```

---

## Views (apps/*/views.py)

### Class-Based Views
```python
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404

class ExampleListView(LoginRequiredMixin, ListView):
    model = Example
    template_name = 'app/example_list.html'
    context_object_name = 'examples'
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        return Example.objects.filter(user=self.request.user).select_related('user')
    
    def form_valid(self, form):
        messages.success(self.request, 'Created successfully!')
        return super().form_valid(form)
```

### Key Conventions
- Use `LoginRequiredMixin` for authenticated views
- Always define `login_url` for LoginRequiredMixin
- Use `get_object_or_404` for single object retrieval
- Use `select_related()` and `prefetch_related()` for query optimization
- Use Django `messages` framework for user feedback

---

## Forms (apps/*/forms.py)

```python
from django import forms
from django.core.exceptions import ValidationError
from .models import Example

class ExampleForm(forms.ModelForm):
    class Meta:
        model = Example
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Example.objects.filter(name=name).exists():
            raise ValidationError("Example with this name already exists.")
        return name
```

### Key Conventions
- Inherit from `forms.ModelForm` or `forms.Form`
- Use `widget_tweaks` compatible class names (e.g., `form-control`)
- Define `clean_<fieldname>` methods for validation

---

## Admin (apps/*/admin.py)

```python
from django.contrib import admin
from .models import Example

@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    actions = ['approve_examples']
    
    def approve_examples(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_examples.short_description = "Approve selected"
```

### Key Conventions
- Use `@admin.register(Model)` decorator
- Use `fieldsets` for organized field grouping
- Define `readonly_fields` for auto-generated timestamps
- Use `list_editable` for quick inline changes
- Define actions for bulk operations

---

## URL Patterns (apps/*/urls.py)

```python
from django.urls import path
from .views import ExampleListView, ExampleCreateView

app_name = 'examples'

urlpatterns = [
    path('', ExampleListView.as_view(), name='list'),
    path('create/', ExampleCreateView.as_view(), name='create'),
]
```

### Key Conventions
- Always use `app_name` namespace
- Use `reverse_lazy` for class-based view success URLs
- Use named groups in URL patterns

---

## Template Conventions

### Directory Structure
```
templates/
├── base.html                    # Base template with design system
├── partials/
│   ├── header.html
│   ├── footer.html
│   └── messages.html
├── pages/
│   ├── home.html
│   ├── about.html
│   ├── contact.html
│   ├── faq.html
│   └── partials/
├── products/
│   ├── catalog.html
│   ├── product_detail.html
│   └── partials/
├── accounts/
└── orders/
```

### Template Variables (from Context Processors)
- `{{ site_name }}` - Site name (default: "Lifeline Healthcare")
- `{{ site_tagline }}` - Site tagline
- `{{ site_settings }}` - Dict of all SiteConfiguration values
- `{{ navigation }}` - Main menu and categories
- `{{ contact_email }}`, `{{ contact_phone }}`

### Design System (CSS Variables in base.html)
```css
--color-primary: #0c7ff2;
--color-primary-hover: #0968da;
--color-surface: #ffffff;
--color-surface-muted: #f8fafc;
--color-content-primary: #0f172a;
--color-content-secondary: #64748b;
--color-border: #e2e8f0;
--color-success: #059669;
--color-warning: #d97706;
--color-error: #dc2626;
--color-info: #0284c7;
```

### Fonts
- **Headings**: Lexend (Google Fonts)
- **Body**: Inter (Google Fonts)

### Key Conventions
- Template directories: `templates/<app_name>/<model_name>.html`
- Use Tailwind CSS classes for styling
- Use `{% url 'app_name:view_name' %}` for links
- Use `{% load static %}` for static files
- Use `{% include 'partials/file.html' %}` for reusable components
- Use `{% block content %}{% endblock %}` for page content

---

## Testing Conventions

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Example

User = get_user_model()

class ExampleTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_example_creation(self):
        example = Example.objects.create(name='Test', user=self.user)
        self.assertEqual(example.name, 'Test')
        self.assertEqual(example.user, self.user)
    
    def test_failure_case(self):
        with self.assertRaises(ValidationError):
            # Test validation failures
            pass
```

### Key Conventions
- Use `django.test.TestCase`
- Name test classes as `<ModelName>TestCase`
- Name test methods as `test_<description>`
- Use `setUp` for test data creation
- Test both success and failure cases
- Use `assertEqual`, `assertTrue`, `assertFalse`, `assertRaises`

---

## Common Patterns

### User Type Checking
```python
if user.user_type == 'PATIENT':
    # Patient-specific logic
elif user.user_type == 'PHARMACY':
    # Pharmacy-specific logic
```

### Price Display Based on User
```python
price = product.get_price_for_user(request.user)  # Returns pharmacy or patient price
discount = product.get_discount_percentage(request.user)
```

### Slug Auto-generation
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.name)
    super().save(*args, **kwargs)
```

### Image Storage (Base64)
```python
import base64
from PIL import Image
from io import BytesIO

def save_image_as_base64(self, image_file):
    img = Image.open(image_file)
    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=85)
    self.image_data = base64.b64encode(img_io.read()).decode('utf-8')
```

---

## Project Structure
```
lifeline_healthcare/
├── apps/
│   ├── accounts/      # User auth, profiles, addresses
│   ├── cart/          # Shopping cart, wishlist
│   ├── core/          # Base models, site config, pages
│   ├── orders/        # Order processing, tracking
│   └── products/      # Product catalog, categories
├── pharma_ecommerce/  # Django settings
├── templates/         # Base templates
├── static/            # CSS, JS, images
│   ├── css/
│   │   ├── tailwind.min.css
│   │   └── custom.css   # Design system, animations
│   └── js/
├── logs/              # Application logs
├── AGENTS.md          # This file
├── manage.py
└── requirements.txt
```

---

## Important Notes

1. **Always run** `python manage.py check` before committing
2. **Create migrations** after model changes: `python manage.py makemigrations`
3. **Use `get_user_model()`** instead of importing User directly
4. **Use timezone-aware datetime**: `from django.utils import timezone`
5. **No linter configured** - follow PEP 8 manually
6. **Dependencies**: Django 5.2.4, Pillow, django-widget-tweaks, python-decouple
