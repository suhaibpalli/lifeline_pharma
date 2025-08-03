from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.ContactSuccessView.as_view(), name='contact_success'),
    path('page/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
    path('check-delivery/', views.check_delivery_zone, name='check_delivery'),
]
