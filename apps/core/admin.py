from django.contrib import admin
from .models import SiteConfiguration, ContactInquiry, DeliveryZone, Page, CarouselImage

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'description']
    list_editable = ['is_active']

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_resolved.short_description = "Mark selected inquiries as resolved"
    
    actions = [mark_resolved]

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'pincode_start', 'pincode_end', 'delivery_charge', 'is_serviceable']
    list_filter = ['is_serviceable', 'estimated_days']
    search_fields = ['name', 'pincode_start', 'pincode_end']

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'updated_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']

    fieldsets = (
        ('Image Content', {
            'fields': ('title', 'subtitle', 'image_upload', 'button_text', 'button_link')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('System Fields', {
            'fields': ('image_data',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['image_data']

    # no special get_form/get_fieldsets overrides needed anymore
    # model.save() handles conversion from image_upload -> image_data
