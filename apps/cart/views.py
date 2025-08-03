from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import F
import json

from apps.products.models import Product
from .models import Cart, CartItem, Wishlist
from .utils import get_or_create_cart, get_cart_context

class CartView(TemplateView):
    """Cart page view"""
    template_name = 'cart/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('product', 'product__manufacturer').all()
        return context

@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check stock
        if product.track_inventory and product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': 'Insufficient stock available',
                'stock_available': product.stock_quantity
            })
        
        cart = get_or_create_cart(request)
        
        # Get current price for user
        if request.user.is_authenticated:
            price = product.get_price_for_user(request.user)
        else:
            price = product.patient_price
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': price}
        )
        
        if not created:
            # Item already exists, update quantity
            new_quantity = cart_item.quantity + quantity
            
            # Check stock again
            if product.track_inventory and product.stock_quantity < new_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock_quantity} items available',
                    'current_quantity': cart_item.quantity
                })
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        cart_context = get_cart_context(request)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_items_count': cart_context['cart_items_count'],
            'cart_subtotal': float(cart_context['cart_subtotal']),
            'item_quantity': cart_item.quantity
        })
        
    except (ValueError, KeyError, Product.DoesNotExist) as e:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request'
        })

@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity <= 0:
            return remove_cart_item(request, item_id)
        
        # Check stock
        if cart_item.product.track_inventory and cart_item.product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.product.stock_quantity} items available'
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        cart_context = get_cart_context(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cart_items_count': cart_context['cart_items_count'],
            'cart_subtotal': float(cart_context['cart_subtotal']),
            'item_total': float(cart_item.total_price)
        })
        
    except (ValueError, KeyError, CartItem.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Invalid request'
        })

@require_POST
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()
        
        cart_context = get_cart_context(request)
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_items_count': cart_context['cart_items_count'],
            'cart_subtotal': float(cart_context['cart_subtotal'])
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })

def clear_cart(request):
    """Clear entire cart"""
    cart = get_or_create_cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart:cart')

# Wishlist Views
class WishlistView(LoginRequiredMixin, ListView):
    """User wishlist view"""
    model = Wishlist
    template_name = 'cart/wishlist.html'
    context_object_name = 'wishlist_items'
    login_url = '/accounts/login/'

    def get_queryset(self):
        return (
            Wishlist.objects
            .filter(user=self.request.user)
            .select_related('product', 'product__manufacturer')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Attach a `user_price` attribute to each wishlist item
        for item in context['wishlist_items']:
            item.user_price = item.product.get_price_for_user(self.request.user)
        return context

@login_required
@require_POST
def add_to_wishlist(request):
    """Add product to wishlist"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            message = f'{product.name} added to wishlist'
        else:
            message = f'{product.name} is already in your wishlist'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'added': created
        })
        
    except (ValueError, KeyError, Product.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Invalid request'
        })

@login_required
@require_POST
def remove_from_wishlist(request, item_id):
    """Remove item from wishlist"""
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from wishlist'
        })
        
    except Wishlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })

@login_required
@require_POST
def move_to_cart(request, item_id):
    """Move item from wishlist to cart"""
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        product = wishlist_item.product
        
        # Add to cart
        cart = get_or_create_cart(request)
        price = product.get_price_for_user(request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1, 'price': price}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Remove from wishlist
        wishlist_item.delete()
        
        cart_context = get_cart_context(request)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} moved to cart',
            'cart_items_count': cart_context['cart_items_count']
        })
        
    except Wishlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })
