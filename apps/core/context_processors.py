import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def site_settings(request):
    settings_dict = cache.get("site_settings_dict")
    if settings_dict is None:
        settings_dict = {}
        try:
            from .models import SiteConfiguration

            for setting in SiteConfiguration.objects.filter(is_active=True):
                settings_dict[setting.key] = setting.value
            cache.set("site_settings_dict", settings_dict, timeout=3600)
        except Exception as e:
            logger.error("Failed to load SiteConfiguration: %s", e)
    return {
        "site_settings": settings_dict,
        "site_name": settings_dict.get("site_name", "Lifeline Healthcare"),
        "site_tagline": settings_dict.get(
            "site_tagline", "Your trusted online pharmacy for genuine medicines"
        ),
        "contact_email": settings_dict.get("contact_email", ""),
        "contact_phone": settings_dict.get("contact_phone", ""),
    }


def navigation_context(request):
    categories = cache.get("nav_categories")
    if categories is None:
        try:
            from apps.products.models import Category

            categories = list(
                Category.objects.filter(is_active=True, parent=None).only(
                    "id", "name", "slug"
                )[:6]
            )
            cache.set("nav_categories", categories, timeout=1800)
        except Exception as e:
            logger.error("Failed to load nav categories: %s", e)
            categories = []

    current_url = request.resolver_match.url_name if request.resolver_match else ""
    return {
        "navigation": {
            "main_menu": [
                {"name": "Home", "url": "/", "active": current_url == "home"},
                {
                    "name": "Products",
                    "url": "/products/",
                    "active": "products" in request.path,
                },
                {"name": "About", "url": "/about/", "active": current_url == "about"},
                {
                    "name": "Contact",
                    "url": "/contact/",
                    "active": current_url == "contact",
                },
            ],
            "categories": categories,
        }
    }
