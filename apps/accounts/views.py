import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import CustomUser, PatientProfile, PharmacyProfile, Address, EmailVerification
from .forms import (
    PatientRegistrationForm, 
    PharmacyRegistrationForm, 
    CustomAuthenticationForm,
    AddressForm,
    ProfileUpdateForm
)

class RegisterChoiceView(TemplateView):
    """User type selection view"""
    template_name = 'accounts/register_choice.html'

class PatientRegistrationView(CreateView):
    """Patient registration view"""
    model = CustomUser
    form_class = PatientRegistrationForm
    template_name = 'accounts/patient_register.html'
    success_url = reverse_lazy('accounts:registration_success')
    
    def form_valid(self, form):
        # Let CreateView do the one save (which calls form.save())
        response = super().form_valid(form)

        # self.object is now the newly created user (and profile)
        # Send verification email (we’ll implement this later)
        # send_verification_email(self.object)

        messages.success(
            self.request,
            'Registration successful! Please check your email to verify your account.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'There were errors in your registration. Please correct them below.'
        )
        return super().form_invalid(form)

class PharmacyRegistrationView(CreateView):
    """Pharmacy registration view"""
    model = CustomUser
    form_class = PharmacyRegistrationForm
    template_name = 'accounts/pharmacy_register.html'
    success_url = reverse_lazy('accounts:registration_success')
    
    def form_valid(self, form):
        # Let Django do its one form.save() (which also creates the PharmacyProfile)
        response = super().form_valid(form)

        # Now self.object is the newly-created CustomUser
        license_file = self.request.FILES.get('license_document')
        if license_file:
            import base64
            file_content = license_file.read()
            encoded_file = base64.b64encode(file_content).decode('utf-8')
            # update the one profile you already created
            self.object.pharmacy_profile.license_document = encoded_file
            self.object.pharmacy_profile.save()

        messages.success(
            self.request,
            'Registration successful! Your pharmacy account is pending approval. We will notify you once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'There were errors in your registration. Please correct them below.'
        )
        return super().form_invalid(form)

class RegistrationSuccessView(TemplateView):
    """Registration success page"""
    template_name = 'accounts/registration_success.html'

class CustomLoginView(TemplateView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self._redirect_user(request.user)
        
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = CustomAuthenticationForm(data=request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Set session expiry based on remember me
                if not remember_me:
                    request.session.set_expiry(0)  # Browser session
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
                return self._redirect_user(user)
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
        
        return render(request, self.template_name, {'form': form})
    
    def _redirect_user(self, user):
        """Redirect user based on their type"""
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        
        # Temporarily redirect all users to profile until dashboard is built
        return redirect('accounts:profile')
        
        # Later when dashboard is ready, uncomment this:
        # if user.user_type == 'ADMIN':
        #     return redirect('admin_panel:dashboard')
        # elif user.user_type == 'PHARMACY':
        #     return redirect('dashboard:pharmacy_dashboard')
        # else:  # PATIENT
        #     return redirect('dashboard:patient_dashboard')

def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('core:home')

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    login_url = '/accounts/login/'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['addresses'] = user.addresses.all()
        context['profile_form'] = ProfileUpdateForm(instance=user)
        
        if user.user_type == 'PATIENT':
            context['patient_profile'] = user.patient_profile
        elif user.user_type == 'PHARMACY':
            context['pharmacy_profile'] = user.pharmacy_profile
            
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Profile update view"""
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = '/accounts/login/'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class AddressListView(LoginRequiredMixin, ListView):
    """Address list view"""
    model = Address
    template_name = 'accounts/address_list.html'
    context_object_name = 'addresses'
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

class AddressCreateView(LoginRequiredMixin, CreateView):
    """Address create view"""
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:address_list')
    login_url = '/accounts/login/'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Address added successfully!')
        return super().form_valid(form)

class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """Address update view"""
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:address_list')
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully!')
        return super().form_valid(form)

@login_required
def delete_address(request, pk):
    """Delete address view"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('accounts:address_list')
    
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})

def verify_email(request, token):
    """Email verification view"""
    try:
        verification = EmailVerification.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        user = verification.user
        user.is_verified = True
        user.save()
        
        verification.is_used = True
        verification.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('core:home')

def check_email_exists(request):
    """AJAX view to check if email exists"""
    if request.method == 'GET':
        email = request.GET.get('email')
        exists = CustomUser.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})
    
    return JsonResponse({'error': 'Invalid request'})

# Utility functions for email verification (to be implemented later)
def send_verification_email(user):
    """Send verification email to user"""
    # Create verification token
    token = str(uuid.uuid4())
    expires_at = timezone.now() + timedelta(days=1)
    
    EmailVerification.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    # Send email (we'll implement this when we configure email)
    verification_url = f"{settings.SITE_URL}/accounts/verify-email/{token}/"
    
    # For now, just print the URL (you can implement actual email sending later)
    print(f"Verification URL for {user.email}: {verification_url}")
