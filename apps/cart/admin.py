from django.contrib import admin
from .models import Cart, CartItem, Wishlist

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_items', 'subtotal', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['created_at']
    search_fields = ['cart__user__email', 'product__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
