from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.conf import settings
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from .models import CarouselImage, ContactInquiry, Page, DeliveryZone, RetailerEnquiry, ProductCatalogue, DoctorVisitRequest
from .forms import ContactForm, RetailerEnquiryForm, DoctorVisitRequestForm
from django.core.mail import send_mail
from django.conf import settings


class StaticPageMixin:
    page_slug = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.page_slug:
            context["page"] = Page.objects.filter(
                slug=self.page_slug, is_published=True
            ).first()
        return context


class HomeView(TemplateView):
    """Homepage view"""

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Welcome to Pharma Store"

        # Get active carousel images
        carousel_images = CarouselImage.objects.filter(is_active=True)
        context["carousel_images"] = carousel_images

        try:
            from apps.products.models import Product

            featured = list(
                Product.objects.filter(is_active=True, is_featured=True)
                .select_related("manufacturer", "category")
                .prefetch_related("images")[:12]
            )
            if not featured:
                featured = list(
                    Product.objects.filter(is_active=True)
                    .select_related("manufacturer", "category")
                    .prefetch_related("images")
                    .order_by("-created_at")[:12]
                )
            for product in featured:
                product.user_price = product.get_price_for_user(self.request.user)
                product.discount_percentage = product.get_discount_percentage(self.request.user)
            context["featured_products"] = featured
        except Exception:
            context["featured_products"] = []

        return context


class AboutView(StaticPageMixin, TemplateView):
    """About us page"""

    template_name = "pages/about.html"
    page_slug = "about-us"


class ContactView(CreateView):
    """Contact us page with form"""

    model = ContactInquiry
    form_class = ContactForm
    template_name = "pages/contact.html"
    success_url = reverse_lazy("core:contact_success")

    def form_valid(self, form):
        messages.success(
            self.request, "Thank you for your message. We will get back to you soon!"
        )
        return super().form_valid(form)


class ContactSuccessView(TemplateView):
    """Contact form success page"""

    template_name = "pages/contact_success.html"


class PageDetailView(TemplateView):
    """Generic page detail view for static pages"""

    template_name = "pages/page_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs.get("slug")
        page = get_object_or_404(Page, slug=slug, is_published=True)
        context["page"] = page
        return context


def check_delivery_zone(request):
    """AJAX view to check if delivery is available for a pincode"""
    if request.method == "GET":
        pincode = request.GET.get("pincode")
        if pincode:
            try:
                zone = DeliveryZone.objects.filter(
                    pincode_start__lte=pincode,
                    pincode_end__gte=pincode,
                    is_serviceable=True,
                ).first()

                if zone:
                    return JsonResponse(
                        {
                            "serviceable": True,
                            "delivery_charge": float(zone.delivery_charge),
                            "estimated_days": zone.estimated_days,
                            "zone_name": zone.name,
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "serviceable": False,
                            "message": "Sorry, we do not deliver to this pincode yet.",
                        }
                    )
            except Exception as e:
                return JsonResponse({"error": "Unable to check delivery availability."})

    return JsonResponse({"error": "Invalid request"})


def chrome_devtools_manifest(request):
    """Silence Chrome DevTools well-known probe in local development."""
    return HttpResponse(status=204)


def robots_txt(request):
    """Serve crawler rules and sitemap location."""
    site_url = settings.SITE_URL.rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /cart/",
        "Disallow: /orders/",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


class FAQView(TemplateView):
    """FAQ page"""

    template_name = "pages/faq.html"


class PrivacyPolicyView(TemplateView):
    """Privacy Policy page"""

    template_name = "pages/privacy_policy.html"


class TermsOfServiceView(TemplateView):
    """Terms of Service page"""

    template_name = "pages/terms_of_service.html"


# Health check endpoint
def health_check(request):
    """Used by Docker HEALTHCHECK and Uptime Kuma."""
    from django.db import connection
    from django.core.cache import cache

    checks = {}
    status = 200

    # Database
    try:
        connection.ensure_connection()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
        status = 503

    # Cache / Redis
    try:
        cache.set("health_check", "ok", timeout=5)
        assert cache.get("health_check") == "ok"
        checks["cache"] = "ok"
    except Exception as e:
        checks["cache"] = f"error: {e}"

    return JsonResponse(
        {"status": "ok" if status == 200 else "degraded", **checks}, status=status
    )


# Error handlers
def custom_404(request, exception):
    """Custom 404 error page"""
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, "errors/500.html", status=500)

class RetailerEnquiryView(CreateView):
    model = RetailerEnquiry
    form_class = RetailerEnquiryForm
    template_name = 'pages/retailer_enquiry.html'
    success_url = reverse_lazy('core:retailer_enquiry_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        subject = f"[Pharma Store] New Retailer Enquiry Submission"
        message = f"New Retailer Enquiry from {form.cleaned_data['business_name']}:\n\n"
        for field, value in form.cleaned_data.items():
            message += f"{field.replace('_', ' ').title()}: {value}\n"
        
        from .models import SiteConfiguration
        admin_email = settings.DEFAULT_FROM_EMAIL
        try:
            admin_email = SiteConfiguration.objects.get(key='contact_email').value
        except SiteConfiguration.DoesNotExist:
            pass
            
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        except Exception:
            pass
            
        messages.success(self.request, 'Your enquiry has been submitted successfully!')
        return response

class RetailerEnquirySuccessView(TemplateView):
    template_name = 'pages/retailer_enquiry_success.html'

class DoctorVisitRequestView(CreateView):
    model = DoctorVisitRequest
    form_class = DoctorVisitRequestForm
    template_name = 'pages/doctor_visit_request.html'
    success_url = reverse_lazy('core:doctor_visit_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        subject = f"[Pharma Store] New Doctor Visit Request Submission"
        message = f"New Visit Request from Dr. {form.cleaned_data['doctor_name']}:\n\n"
        for field, value in form.cleaned_data.items():
            message += f"{field.replace('_', ' ').title()}: {value}\n"
            
        from .models import SiteConfiguration
        admin_email = settings.DEFAULT_FROM_EMAIL
        try:
            admin_email = SiteConfiguration.objects.get(key='contact_email').value
        except SiteConfiguration.DoesNotExist:
            pass
            
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        except Exception:
            pass
            
        messages.success(self.request, 'Your visit request has been submitted successfully!')
        return response

class DoctorVisitSuccessView(TemplateView):
    template_name = 'pages/doctor_visit_success.html'

class CatalogueView(TemplateView):
    template_name = 'pages/catalogue.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalogue'] = ProductCatalogue.objects.filter(is_active=True).first()
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        if name and phone:
            # Save as ContactInquiry for lead capture
            ContactInquiry.objects.create(
                name=name,
                phone=phone,
                email='lead@catalogue.com',
                subject='Catalogue Download Lead',
                message=f'Lead captured from catalogue download. Phone: {phone}'
            )
            # Store flag in session to allow download
            request.session['catalogue_unlocked'] = True
            messages.success(request, 'Thank you! You can now download the catalogue.')
            
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class CareersView(TemplateView):
    template_name = 'pages/careers.html'

class ReturnPolicyView(TemplateView):
    template_name = 'pages/return_policy.html'

class DeliveryAreasView(TemplateView):
    template_name = 'pages/delivery_areas.html'

class PharmaciesView(TemplateView):
    template_name = 'pages/pharmacies.html'

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            ContactInquiry.objects.create(
                name="Newsletter Subscriber",
                email=email,
                subject="Newsletter Subscription",
                message="Subscribed to newsletter."
            )
            messages.success(request, 'Check your email for confirmation')
    from django.shortcuts import redirect
    return redirect(request.META.get('HTTP_REFERER', '/'))
