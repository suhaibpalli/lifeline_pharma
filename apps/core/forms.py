from django import forms
from .models import ContactInquiry, RetailerEnquiry, DoctorVisitRequest

class ContactForm(forms.ModelForm):
    """Contact form"""
    
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': '+91 9876543210'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'What is this regarding?'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Your message...',
                'rows': 5
            }),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

class RetailerEnquiryForm(forms.ModelForm):
    """Retailer Enquiry form"""
    
    class Meta:
        model = RetailerEnquiry
        fields = ['business_name', 'contact_person', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'gst_number', 'estimated_order_value', 'message']
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Business Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Contact Person Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Business Address', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Pincode'}),
            'gst_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'GST Number (Optional)'}),
            'estimated_order_value': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'}),
            'message': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Message/Requirements (Optional)', 'rows': 4}),
        }

class DoctorVisitRequestForm(forms.ModelForm):
    """Doctor Visit Request form"""
    
    class Meta:
        model = DoctorVisitRequest
        fields = ['doctor_name', 'specialization', 'hospital_name', 'email', 'phone', 'address', 'city', 'state', 'preferred_date', 'preferred_time', 'purpose', 'notes']
        widgets = {
            'doctor_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Doctor Name'}),
            'specialization': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'}),
            'hospital_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Hospital/Clinic Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Address', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'State'}),
            'preferred_date': forms.DateInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'type': 'date'}),
            'preferred_time': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'}),
            'purpose': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Purpose of Visit (Optional)', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Additional Notes (Optional)', 'rows': 3}),
        }
