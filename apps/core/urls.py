from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path(
        "contact/success/", views.ContactSuccessView.as_view(), name="contact_success"
    ),
    path("faq/", views.FAQView.as_view(), name="faq"),
    path("privacy-policy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path(
        "terms-of-service/", views.TermsOfServiceView.as_view(), name="terms_of_service"
    ),
    path("page/<slug:slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("check-delivery/", views.check_delivery_zone, name="check_delivery"),
]
