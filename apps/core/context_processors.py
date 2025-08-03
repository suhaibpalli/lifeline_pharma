from .models import SiteConfiguration

def site_settings(request):
    """Add site-wide settings to template context"""
    settings_dict = {}
    
    try:
        settings = SiteConfiguration.objects.filter(is_active=True)
        for setting in settings:
            settings_dict[setting.key] = setting.value
    except:
        pass
    
    return {
        'site_settings': settings_dict,
        'site_name': settings_dict.get('site_name', 'Pharma Store'),
        'site_tagline': settings_dict.get('site_tagline', 'Your trusted pharmacy partner'),
        'contact_email': settings_dict.get('contact_email', 'info@pharmastore.com'),
        'contact_phone': settings_dict.get('contact_phone', '+91 9876543210'),
    }

def navigation_context(request):
    """Add navigation context"""
    # Import here to avoid circular imports
    from apps.products.models import Category

    try:
        categories = Category.objects.filter(is_active=True, parent=None)[:6]
    except:
        categories = []

    navigation = {
        'main_menu': [
            {'name': 'Home', 'url': '/', 'active': request.resolver_match.url_name == 'home'},
            {'name': 'Products', 'url': '/products/', 'active': 'products' in request.path},
            {'name': 'About', 'url': '/about/', 'active': request.resolver_match.url_name == 'about'},
            {'name': 'Contact', 'url': '/contact/', 'active': request.resolver_match.url_name == 'contact'},
        ],
        'categories': categories
    }
    
    return {'navigation': navigation}
