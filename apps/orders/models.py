import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.urls import reverse
from apps.core.models import TimeStampedModel
from apps.products.models import Product
from apps.accounts.models import Address

User = get_user_model()

class Order(TimeStampedModel):
    """Main order model"""
    
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
        ('WALLET', 'Wallet'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    
    # Order Identification
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Order Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Information
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='COD')
    payment_id = models.CharField(max_length=100, blank=True)  # Transaction ID from payment gateway
    
    # Delivery Information
    delivery_address = models.JSONField()  # Store complete address as JSON
    delivery_phone = models.CharField(max_length=15)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    prescription_required = models.BooleanField(default=False)
    prescription_image = models.TextField(blank=True)  # Base64 encoded prescription
    
    # Tracking
    tracking_number = models.CharField(max_length=50, blank=True)
    courier_partner = models.CharField(max_length=100, blank=True)
    
    # Admin fields
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_orders'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        from django.utils import timezone
        
        # Format: ORD-YYYYMMDD-XXXXXX
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"ORD-{date_str}-{random_str}"
    
    def get_absolute_url(self):
        return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['PENDING', 'CONFIRMED'] and self.payment_status != 'PAID'
    
    @property
    def is_delivered(self):
        return self.status == 'DELIVERED'
    
    @property
    def requires_prescription(self):
        """Check if any item in order requires prescription"""
        return self.items.filter(product__prescription_required='RX').exists()

class OrderItem(TimeStampedModel):
    """Individual order items"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        unique_together = ['order', 'product']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.order_number})"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

class OrderStatusHistory(TimeStampedModel):
    """Track order status changes"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order.order_number} - {self.get_status_display()}"

class OrderRefund(TimeStampedModel):
    """Handle order refunds"""
    
    REFUND_STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('PROCESSED', 'Processed'),
        ('REJECTED', 'Rejected'),
    ]
    
    REFUND_TYPE_CHOICES = [
        ('FULL', 'Full Refund'),
        ('PARTIAL', 'Partial Refund'),
        ('ITEM', 'Item Refund'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    refund_type = models.CharField(max_length=10, choices=REFUND_TYPE_CHOICES, default='FULL')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=REFUND_STATUS_CHOICES, default='REQUESTED')
    
    # Admin fields
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_refunds'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Order Refund"
        verbose_name_plural = "Order Refunds"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund for Order #{self.order.order_number} - ₹{self.amount}"

class Coupon(TimeStampedModel):
    """Discount coupons"""
    
    COUPON_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('FREE_DELIVERY', 'Free Delivery'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    coupon_type = models.CharField(max_length=15, choices=COUPON_TYPE_CHOICES, default='PERCENTAGE')
    value = models.DecimalField(max_digits=10, decimal_places=2)  # Percentage or fixed amount
    
    # Usage limits
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # Total usage limit
    usage_limit_per_user = models.PositiveIntegerField(default=1)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid_for_user(self, user, order_amount):
        """Check if coupon is valid for user and order"""
        from django.utils import timezone
        
        # Check if active
        if not self.is_active:
            return False, "Coupon is not active"
        
        # Check validity period
        now = timezone.now()
        if now < self.start_date or now > self.end_date:
            return False, "Coupon has expired"
        
        # Check minimum amount
        if order_amount < self.minimum_amount:
            return False, f"Minimum order amount is ₹{self.minimum_amount}"
        
        # Check total usage limit
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Coupon usage limit exceeded"
        
        # Check per-user usage limit
        if user.is_authenticated:
            user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_usage >= self.usage_limit_per_user:
                return False, "You have already used this coupon"
        
        return True, "Valid"
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount"""
        if self.coupon_type == 'PERCENTAGE':
            discount = (order_amount * self.value) / 100
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
        elif self.coupon_type == 'FIXED':
            discount = min(self.value, order_amount)
        else:  # FREE_DELIVERY
            discount = 0  # Handle in delivery charge calculation
        
        return discount

class CouponUsage(TimeStampedModel):
    """Track coupon usage"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.coupon.code} used in Order #{self.order.order_number}"
