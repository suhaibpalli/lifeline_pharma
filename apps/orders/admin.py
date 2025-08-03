from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage, OrderRefund

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['total_price']
    extra = 0

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    readonly_fields = ['created_at']
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 'total_amount', 
        'payment_method', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'payment_method', 'created_at', 
        'prescription_required'
    ]
    search_fields = ['order_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'delivery_address'
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'delivery_charge', 'discount_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_id')
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_phone', 'estimated_delivery', 'actual_delivery')
        }),
        ('Additional Info', {
            'fields': ('notes', 'prescription_required', 'tracking_number', 'courier_partner'),
            'classes': ('collapse',)
        }),
        ('Admin Fields', {
            'fields': ('processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered']
    
    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='CONFIRMED',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        
        # Create status history for each order
        for order in queryset.filter(status='CONFIRMED'):
            OrderStatusHistory.objects.create(
                order=order,
                status='CONFIRMED',
                notes='Confirmed by admin',
                changed_by=request.user
            )
        
        self.message_user(request, f'{updated} orders marked as confirmed.')
    mark_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_shipped(self, request, queryset):
        updated = queryset.filter(status__in=['CONFIRMED', 'PROCESSING']).update(
            status='SHIPPED',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_delivered(self, request, queryset):
        updated = queryset.filter(status='OUT_FOR_DELIVERY').update(
            status='DELIVERED',
            actual_delivery=timezone.now()
        )
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_delivered.short_description = "Mark selected orders as delivered"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__status', 'created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'coupon_type', 'value', 'usage_count', 
        'is_active', 'start_date', 'end_date'
    ]
    list_filter = ['coupon_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['code', 'name']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Settings', {
            'fields': ('coupon_type', 'value', 'minimum_amount', 'maximum_discount')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'usage_count')
        }),
        ('Validity', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'discount_amount', 'created_at']
    list_filter = ['coupon', 'created_at']
    search_fields = ['coupon__code', 'user__email', 'order__order_number']
    readonly_fields = ['created_at']

@admin.register(OrderRefund)
class OrderRefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'refund_type', 'amount', 'status', 'created_at']
    list_filter = ['refund_type', 'status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['created_at', 'updated_at']
