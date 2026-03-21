# Agent Guidelines for Lifeline Healthcare Project

## Project Overview
Django 5.2.4 e-commerce platform for pharmacy/healthcare with:
- Custom user authentication (email-based)
- Multiple user types: PATIENT, PHARMACY, ADMIN
- Product catalog with prescription management
- Order processing and tracking
- Shopping cart functionality

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

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check
python manage.py check --deploy
```

## Code Style Guidelines

### Python Style
- Follow PEP 8 with 4-space indentation
- Maximum line length: 120 characters
- Use type hints where beneficial
- Docstrings for classes and public methods using triple quotes

### Imports
```python
# Standard library first
import uuid
from decimal import Decimal
from datetime import timedelta

# Django core
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

# Third party
from django.utils.text import slugify

# Local imports - use relative imports within apps
from apps.core.models import TimeStampedModel
from .models import CustomUser
```

### Models (apps/*/models.py)
- All models inherit from `TimeStampedModel` for created_at/updated_at
- Use `django.utils.translation.gettext_lazy as _` for verbose names
- Define CHOICES as class-level constants (uppercase)
- Use `related_name` on ForeignKey fields
- Always define `__str__` method
- Use `@property` for computed fields
- Avoid business logic in models; keep them for data structure only
- Use `blank=True` for optional fields, `null=True` for database nullable

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
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

### Views (apps/*/views.py)
- Use class-based views (CreateView, UpdateView, ListView, DetailView)
- Use `LoginRequiredMixin` for authenticated views
- Use `get_object_or_404` for single object retrieval
- Use `messages` framework for user feedback
- Always define `login_url` for LoginRequiredMixin
- Use `select_related` and `prefetch_related` for query optimization

```python
from django.views.generic import CreateView, ListView
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

### Forms (apps/*/forms.py)
- Inherit from `forms.ModelForm` or `forms.Form`
- Define `Meta` class with `model` and `fields`
- Use `widget_tweaks` compatible class names for styling
- Define clean methods for validation

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

### Admin (apps/*/admin.py)
- Use `@admin.register(Model)` decorator
- Define `list_display`, `list_filter`, `search_fields`
- Use `readonly_fields` for auto-generated fields
- Define actions for bulk operations

```python
from django.contrib import admin
from .models import Example

@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_examples']
    
    def approve_examples(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_examples.short_description = "Approve selected examples"
```

### URL Patterns (apps/*/urls.py)
- Use `app_name` namespace
- Use `reverse_lazy` for class-based view success URLs

```python
from django.urls import path
from .views import ExampleListView, ExampleCreateView

app_name = 'examples'

urlpatterns = [
    path('', ExampleListView.as_view(), name='list'),
    path('create/', ExampleCreateView.as_view(), name='create'),
]
```

### Testing Conventions
- Use `django.test.TestCase`
- Name test classes as `<ModelName>TestCase`
- Name test methods as `test_<description>`
- Use `setUp` for test data creation
- Test both success and failure cases
- Use `assertEqual`, `assertTrue`, `assertFalse`, etc.

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
```

### Error Handling
- Use try/except for database operations when needed
- Use Django's `messages` framework for user-facing errors
- Return appropriate HTTP status codes for API views
- Log errors using Python's logging module

### Template Conventions
- Template directories: `templates/<app_name>/<model_name>.html`
- Use Bootstrap-compatible class names
- Use `{% url 'app_name:view_name' %}` for links
- Use `{% load static %}` for static files

### Common Patterns
- Base64 image storage: Store images as base64 in `TextField`
- User type checking: `user.user_type == 'PATIENT'`
- Custom managers: Define in `managers.py`
- Abstract base models: Inherit from `TimeStampedModel`
- User-specific queries: Filter by `request.user`

## Project Structure
```
lifeline_healthcare/
├── apps/
│   ├── accounts/     # User authentication, profiles
│   ├── cart/         # Shopping cart
│   ├── core/         # Base models, site configuration
│   ├── orders/       # Order processing
│   └── products/     # Product catalog
├── pharma_ecommerce/ # Django project settings
├── templates/        # Base templates
├── static/           # CSS, JS, images
├── logs/             # Application logs
├── manage.py         # Django CLI
└── requirements.txt   # Python dependencies
```

## Important Notes
- Always run `python manage.py check` before committing
- Create migrations for model changes: `python manage.py makemigrations`
- Use `get_user_model()` instead of importing User model directly
- Remember to include `AUTH_USER_MODEL` setting reference in ForeignKeys
- Use timezone-aware datetime: `from django.utils import timezone`
