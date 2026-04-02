from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    Manufacturer,
    Product,
    ProductReview,
    Stock,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "parent",
        "product_count",
        "is_active",
        "sort_order",
        "image_thumbnail",
    ]
    list_filter = ["is_active", "parent", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active", "sort_order"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")

    def product_count(self, obj):
        return obj.product_count

    product_count.short_description = "Products"

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: auto;" />', obj.image.url
            )
        return "-"

    image_thumbnail.short_description = "Image"


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "product_count",
        "is_active",
        "website_url",
        "logo_thumbnail",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]

    def product_count(self, obj):
        return obj.product_count

    product_count.short_description = "Products"

    def logo_thumbnail(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 50px; height: auto;" />', obj.logo.url
            )
        return "-"

    logo_thumbnail.short_description = "Logo"


class StockInline(admin.TabularInline):
    model = Stock
    extra = 0
    fields = ["movement_type", "quantity", "batch_number", "expiry_date", "notes"]
    readonly_fields = ["created_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "manufacturer",
        "category",
        "patient_price",
        "pharmacy_price",
        "stock_quantity",
        "is_active",
        "is_featured",
    ]
    list_filter = [
        "is_active",
        "is_featured",
        "prescription_required",
        "category",
        "manufacturer",
        "created_at",
    ]
    search_fields = ["name", "description", "manufacturer__name"]
    prepopulated_fields = {"slug": ("name", "manufacturer")}
    list_editable = ["is_active", "is_featured"]
    readonly_fields = ["view_count", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "category", "manufacturer")}),
        (
            "Product Details",
            {
                "fields": (
                    "description",
                    "short_description",
                    "composition",
                    "dosage_form",
                    "strength",
                    "pack_size",
                )
            },
        ),
        (
            "Prescription & Pricing",
            {
                "fields": (
                    "prescription_required",
                    "mrp_price",
                    "patient_price",
                    "pharmacy_price",
                    "cost_price",
                )
            },
        ),
        (
            "Inventory",
            {"fields": ("stock_quantity", "low_stock_threshold", "track_inventory")},
        ),
        ("Status", {"fields": ("is_active", "is_featured")}),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
        (
            "Statistics",
            {
                "fields": ("view_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [StockInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "manufacturer")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "user",
        "rating",
        "is_approved",
        "is_verified_purchase",
        "created_at",
    ]
    list_filter = ["rating", "is_approved", "is_verified_purchase", "created_at"]
    search_fields = ["product__name", "user__email", "title", "review_text"]
    list_editable = ["is_approved"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "user")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "movement_type",
        "quantity",
        "batch_number",
        "expiry_date",
        "created_at",
    ]
    list_filter = ["movement_type", "created_at", "expiry_date"]
    search_fields = ["product__name", "batch_number", "supplier"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "created_by")
