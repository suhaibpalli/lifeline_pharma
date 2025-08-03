from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import ContactInquiry, Page, DeliveryZone
from .forms import ContactForm

class HomeView(TemplateView):
    """Homepage view"""
    template_name = 'pages/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Welcome to Pharma Store'
        # We'll add featured products later
        return context

class AboutView(TemplateView):
    """About us page"""
    template_name = 'pages/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            about_page = Page.objects.get(slug='about-us', is_published=True)
            context['page'] = about_page
        except Page.DoesNotExist:
            context['page'] = None
        return context

class ContactView(CreateView):
    """Contact us page with form"""
    model = ContactInquiry
    form_class = ContactForm
    template_name = 'pages/contact.html'
    success_url = reverse_lazy('core:contact_success')
    
    def form_valid(self, form):
        messages.success(self.request, 'Thank you for your message. We will get back to you soon!')
        return super().form_valid(form)

class ContactSuccessView(TemplateView):
    """Contact form success page"""
    template_name = 'pages/contact_success.html'

class PageDetailView(TemplateView):
    """Generic page detail view for static pages"""
    template_name = 'pages/page_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs.get('slug')
        page = get_object_or_404(Page, slug=slug, is_published=True)
        context['page'] = page
        return context

def check_delivery_zone(request):
    """AJAX view to check if delivery is available for a pincode"""
    if request.method == 'GET':
        pincode = request.GET.get('pincode')
        if pincode:
            try:
                zone = DeliveryZone.objects.filter(
                    pincode_start__lte=pincode,
                    pincode_end__gte=pincode,
                    is_serviceable=True
                ).first()
                
                if zone:
                    return JsonResponse({
                        'serviceable': True,
                        'delivery_charge': float(zone.delivery_charge),
                        'estimated_days': zone.estimated_days,
                        'zone_name': zone.name
                    })
                else:
                    return JsonResponse({
                        'serviceable': False,
                        'message': 'Sorry, we do not deliver to this pincode yet.'
                    })
            except Exception as e:
                return JsonResponse({
                    'error': 'Unable to check delivery availability.'
                })
        
    return JsonResponse({'error': 'Invalid request'})

# Error handlers
def custom_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)
