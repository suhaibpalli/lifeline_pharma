from django.urls import path
from . import views

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
    
    # AJAX URLs
    path('check-email/', views.check_email_exists, name='check_email'),
]
