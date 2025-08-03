import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator

from apps.cart.models import Cart
from apps.cart.utils import get_or_create_cart
from apps.accounts.models import Address
from .models import Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage
from .forms import CheckoutForm, CouponForm
from .utils import calculate_delivery_charge, create_order_from_cart

class OrderListView(LoginRequiredMixin, ListView):
    """User's order list"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('user')

class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__product__manufacturer',
            'status_history'
        )

@login_required
def checkout_view(request):
    """Checkout page"""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart:cart')
    
    # Get user addresses
    addresses = Address.objects.filter(user=request.user)
    
    # Calculate pricing
    subtotal = cart.subtotal
    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create order
                    order = create_order_from_cart(
                        cart=cart,
                        user=request.user,
                        form_data=form.cleaned_data
                    )
                    
                    # Clear cart
                    cart.clear()
                    
                    messages.success(request, f'Order #{order.order_number} placed successfully!')
                    return redirect('orders:order_detail', order_number=order.order_number)
            
            except Exception as e:
                messages.error(request, 'Error placing order. Please try again.')
                
    else:
        initial_data = {}
        if addresses.filter(is_default=True).exists():
            default_address = addresses.filter(is_default=True).first()
            initial_data['address'] = default_address.id
        
        form = CheckoutForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart.items.select_related('product', 'product__manufacturer').all(),
        'addresses': addresses,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'total': total,
    }
    
    return render(request, 'orders/checkout.html', context)

@login_required
@require_POST
def apply_coupon(request):
    """Apply coupon code"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code'
            })
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })
        
        # Calculate cart total
        cart = get_or_create_cart(request)
        subtotal = cart.subtotal
        
        # Validate coupon
        is_valid, message = coupon.is_valid_for_user(request.user, subtotal)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Calculate discount
        discount = coupon.calculate_discount(subtotal)
        delivery_charge = calculate_delivery_charge(subtotal)
        
        if coupon.coupon_type == 'FREE_DELIVERY':
            delivery_charge = 0
            discount = calculate_delivery_charge(subtotal)  # Show delivery charge as discount
        
        total = subtotal + delivery_charge - discount
        
        # Store coupon in session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount': float(discount),
            'type': coupon.coupon_type
        }
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon {coupon.code} applied successfully!',
            'discount': float(discount),
            'delivery_charge': float(delivery_charge),
            'total': float(total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error applying coupon'
        })

@login_required
@require_POST
def remove_coupon(request):
    """Remove applied coupon"""
    request.session.pop('applied_coupon', None)
    
    cart = get_or_create_cart(request)
    subtotal = cart.subtotal
    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge
    
    return JsonResponse({
        'success': True,
        'message': 'Coupon removed',
        'discount': 0,
        'delivery_charge': float(delivery_charge),
        'total': float(total)
    })

@login_required
@require_POST
def cancel_order(request, order_number):
    """Cancel an order"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if not order.can_be_cancelled:
        return JsonResponse({
            'success': False,
            'message': 'This order cannot be cancelled'
        })
    
    try:
        with transaction.atomic():
            # Update order status
            order.status = 'CANCELLED'
            order.save()
            
            # Add status history
            OrderStatusHistory.objects.create(
                order=order,
                status='CANCELLED',
                notes='Cancelled by customer',
                changed_by=request.user
            )
            
            # Restore stock
            for item in order.items.all():
                if item.product.track_inventory:
                    item.product.stock_quantity += item.quantity
                    item.product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Order cancelled successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error cancelling order'
        })

def order_tracking(request, order_number):
    """Public order tracking page"""
    try:
        order = Order.objects.get(order_number=order_number)
        
        # If user is logged in, verify ownership
        if request.user.is_authenticated and order.user != request.user:
            messages.error(request, 'Order not found')
            return redirect('orders:order_list')
        
        context = {
            'order': order,
            'status_history': order.status_history.all()
        }
        
        return render(request, 'orders/order_tracking.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('core:home')
