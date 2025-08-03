import base64
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Manufacturer, Product, ProductImage, ProductReview, Stock, ProductTag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'product_count', 'is_active', 'sort_order']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'sort_order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'is_active', 'website_url']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'

class ProductImageAdminForm(forms.ModelForm):
    # this virtual field will show up as a file‐upload
    image_file = forms.ImageField(
        label="Upload Image",
        required=False,
        help_text="Choose an image file and we'll store it as base64 for you."
    )

    class Meta:
        model = ProductImage
        # note: include only the real model fields plus our new image_file
        fields = ["image_file", "alt_text", "is_primary", "sort_order"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get("image_file")
        if image:
            data = image.read()
            b64 = base64.b64encode(data).decode("utf-8")
            instance.image_data = b64
            # if you want a thumbnail, you could generate/update thumbnail_data here too
            instance.thumbnail_data = b64
        if commit:
            instance.save()
        return instance

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageAdminForm
    fields = ["image_file", "alt_text", "is_primary", "sort_order"]
    readonly_fields = ["created_at"]
    extra = 1

class StockInline(admin.TabularInline):
    model = Stock
    extra = 0
    fields = ['movement_type', 'quantity', 'batch_number', 'expiry_date', 'notes']
    readonly_fields = ['created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'manufacturer', 'category', 'patient_price', 'pharmacy_price', 
        'stock_quantity', 'is_active', 'is_featured'
    ]
    list_filter = [
        'is_active', 'is_featured', 'prescription_required', 
        'category', 'manufacturer', 'created_at'
    ]
    search_fields = ['name', 'description', 'manufacturer__name']
    prepopulated_fields = {'slug': ('name', 'manufacturer')}
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'manufacturer')
        }),
        ('Product Details', {
            'fields': ('description', 'short_description', 'composition', 'dosage_form', 'strength', 'pack_size')
        }),
        ('Prescription & Pricing', {
            'fields': ('prescription_required', 'mrp_price', 'patient_price', 'pharmacy_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'track_inventory')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, StockInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'manufacturer')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'title', 'review_text']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'batch_number', 'expiry_date', 'created_at']
    list_filter = ['movement_type', 'created_at', 'expiry_date']
    search_fields = ['product__name', 'batch_number', 'supplier']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'created_by')

@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Product Count'
