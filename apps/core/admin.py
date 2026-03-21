from django.contrib import admin
from .models import SiteConfiguration, ContactInquiry, DeliveryZone, Page, CarouselImage

# Predefined configuration keys
SITE_CONFIG_KEYS = [
    ("site_name", "Site Name", "text"),
    ("site_tagline", "Site Tagline", "text"),
    ("contact_email", "Contact Email", "email"),
    ("contact_phone", "Contact Phone", "text"),
    ("contact_address", "Contact Address", "textarea"),
    ("meta_description", "Meta Description", "textarea"),
    ("facebook_url", "Facebook URL", "url"),
    ("twitter_url", "Twitter URL", "url"),
    ("instagram_url", "Instagram URL", "url"),
    ("linkedin_url", "LinkedIn URL", "url"),
]


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ["key", "value_preview", "is_active", "updated_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["key", "description"]
    list_editable = ["is_active"]
    ordering = ["key"]

    fieldsets = (
        ("Configuration Details", {"fields": ("key", "value", "description")}),
        ("Status", {"fields": ("is_active",)}),
    )

    def value_preview(self, obj):
        if len(obj.value) > 50:
            return obj.value[:50] + "..."
        return obj.value

    value_preview.short_description = "Value"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            # Make key readonly after creation to prevent issues
            return ["key"]
        return []

    def has_add_permission(self, request):
        # Allow adding new configurations
        return True


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "is_resolved", "created_at"]
    list_filter = ["is_resolved", "created_at"]
    search_fields = ["name", "email", "subject"]
    readonly_fields = ["created_at", "updated_at"]

    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)

    mark_resolved.short_description = "Mark selected inquiries as resolved"

    actions = [mark_resolved]


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "pincode_start",
        "pincode_end",
        "delivery_charge",
        "is_serviceable",
    ]
    list_filter = ["is_serviceable", "estimated_days"]
    search_fields = ["name", "pincode_start", "pincode_end"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_published", "updated_at"]
    list_filter = ["is_published", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ["title", "subtitle", "is_active", "order", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "subtitle"]
    list_editable = ["is_active", "order"]
    ordering = ["order", "-created_at"]

    fieldsets = (
        (
            "Image Content",
            {
                "fields": (
                    "title",
                    "subtitle",
                    "image_upload",
                    "button_text",
                    "button_link",
                )
            },
        ),
        ("Display Settings", {"fields": ("is_active", "order")}),
        ("System Fields", {"fields": ("image_data",), "classes": ("collapse",)}),
    )

    readonly_fields = ["image_data"]

    # no special get_form/get_fieldsets overrides needed anymore
    # model.save() handles conversion from image_upload -> image_data
