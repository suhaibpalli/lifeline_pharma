from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm

app_name = 'accounts'

urlpatterns = [
    # Registration URLs
    path('register/', views.RegisterChoiceView.as_view(), name='register_choice'),
    path('register/patient/', views.PatientRegistrationView.as_view(), name='patient_register'),
    path('register/pharmacy/', views.PharmacyRegistrationView.as_view(), name='pharmacy_register'),
    path('register/success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset URLs
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.txt',
            html_email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done'),
            form_class=CustomPasswordResetForm,
            extra_email_context={'site_name': 'Lifeline Healthcare'}
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    
    # Profile URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # Address URLs
    path('addresses/', views.AddressListView.as_view(), name='address_list'),
    path('addresses/add/', views.AddressCreateView.as_view(), name='address_add'),
    path('addresses/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_edit'),
    path('addresses/<int:pk>/delete/', views.delete_address, name='address_delete'),
    
    # Verification URLs
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path(
        'resend-verification/',
        views.ResendVerificationView.as_view(),
        name='resend_verification',
    ),
    
    # AJAX URLs
    path('check-email/', views.check_email_exists, name='check_email'),
]
