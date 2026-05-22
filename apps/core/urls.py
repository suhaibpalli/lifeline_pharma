from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("contact/success/", views.ContactSuccessView.as_view(), name="contact_success"),
    path("faq/", views.FAQView.as_view(), name="faq"),
    path("privacy-policy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-of-service/", views.TermsOfServiceView.as_view(), name="terms_of_service"),
    path("page/<slug:slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("check-delivery/", views.check_delivery_zone, name="check_delivery"),
    path('retailer-enquiry/', views.RetailerEnquiryView.as_view(), name='retailer_enquiry'),
    path('retailer-enquiry/success/', views.RetailerEnquirySuccessView.as_view(), name='retailer_enquiry_success'),
    path('doctor-visit-request/', views.DoctorVisitRequestView.as_view(), name='doctor_visit_request'),
    path('doctor-visit-request/success/', views.DoctorVisitSuccessView.as_view(), name='doctor_visit_success'),
    path('catalogue/', views.CatalogueView.as_view(), name='catalogue'),
    path('careers/', views.CareersView.as_view(), name='careers'),
    path('return-policy/', views.ReturnPolicyView.as_view(), name='return_policy'),
    path('delivery-areas/', views.DeliveryAreasView.as_view(), name='delivery_areas'),
    path('pharmacies/', views.PharmaciesView.as_view(), name='pharmacies'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
