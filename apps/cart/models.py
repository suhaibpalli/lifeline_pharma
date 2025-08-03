from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from apps.core.models import TimeStampedModel
from apps.products.models import Product
from decimal import Decimal

User = get_user_model()

class Cart(TimeStampedModel):
    """Cart model for both authenticated and guest users"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest Cart ({self.session_key})"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_price(self):
        """Calculate total price (can include delivery charges later)"""
        return self.subtotal
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()

class CartItem(TimeStampedModel):
    """Individual cart item"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of adding
    
    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.quantity * self.price
    
    def save(self, *args, **kwargs):
        # Store current price when adding to cart
        if not self.price:
            if self.cart.user:
                self.price = self.product.get_price_for_user(self.cart.user)
            else:
                self.price = self.product.patient_price
        super().save(*args, **kwargs)

class Wishlist(TimeStampedModel):
    """User wishlist"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"
