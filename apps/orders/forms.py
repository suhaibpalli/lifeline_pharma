from django import forms
from django.contrib.auth import get_user_model
from apps.accounts.models import Address
from .models import Order, Coupon

User = get_user_model()

class CheckoutForm(forms.Form):
    """Checkout form"""
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    ]
    
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        initial='COD'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Any special instructions...',
            'rows': 3
        })
    )
    
    prescription_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'accept': 'image/*'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)
            
            # Style address choices
            self.fields['address'].widget.attrs.update({
                'class': 'address-choice'
            })

class CouponForm(forms.Form):
    """Coupon application form"""
    
    coupon_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Enter coupon code'
        })
    )

class OrderSearchForm(forms.Form):
    """Order search form"""
    
    STATUS_CHOICES = [('', 'All Status')] + Order.ORDER_STATUS_CHOICES
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Search by order number...'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
