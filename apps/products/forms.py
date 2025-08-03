from django import forms
from django.contrib.auth import get_user_model
from .models import Product, ProductReview, Category, Manufacturer
from django.utils.html import mark_safe

User = get_user_model()

class ProductSearchForm(forms.Form):
    """Product search form"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Search medicines, health products...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True, parent=None),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.filter(is_active=True),
        required=False,
        empty_label="All Manufacturers",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Min Price'
        })
    )
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Max Price'
        })
    )
    prescription_required = forms.ChoiceField(
        choices=[('', 'All Products')] + Product.PRESCRIPTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )

class ProductReviewForm(forms.ModelForm):
    """Product review form"""
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'review_text']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
                }
            ),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Review title (optional)'
            }),
            'review_text': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Share your experience with this product...',
                'rows': 4
            }),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating or rating < 1 or rating > 5:
            # Use mark_safe to ensure the error message is not escaped as HTML entities
            raise forms.ValidationError(mark_safe('Please select a valid rating between 1 and 5.'))
        return rating

class ProductFilterForm(forms.Form):
    """Advanced product filtering form"""
    
    SORT_CHOICES = [
        ('name', 'Name (A-Z)'),
        ('-name', 'Name (Z-A)'),
        ('patient_price', 'Price (Low to High)'),
        ('-patient_price', 'Price (High to Low)'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('-view_count', 'Most Popular'),
    ]
    
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
