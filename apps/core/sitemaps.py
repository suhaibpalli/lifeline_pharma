from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.core.models import Page
from apps.products.models import Category, Manufacturer, Product


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return [
            "core:home",
            "core:about",
            "core:contact",
            "core:faq",
            "core:privacy_policy",
            "core:terms_of_service",
            "products:catalog",
        ]

    def location(self, item):
        return reverse(item)


class PageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"
    excluded_slugs = {
        "about",
        "faq",
        "privacy-policy",
        "terms-of-service",
    }

    def items(self):
        return (
            Page.objects.filter(is_published=True)
            .exclude(slug__in=self.excluded_slugs)
            .order_by("-updated_at")
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("core:page_detail", kwargs={"slug": obj.slug})


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Product.objects.filter(is_active=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Category.objects.filter(is_active=True).order_by("sort_order", "name")

    def lastmod(self, obj):
        return obj.updated_at


class ManufacturerSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Manufacturer.objects.filter(is_active=True).order_by("name")

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "pages": PageSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "manufacturers": ManufacturerSitemap,
}
