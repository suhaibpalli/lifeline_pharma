import base64
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from apps.core.models import DeliveryZone
from .models import Order, OrderItem, OrderStatusHistory, CouponUsage

def calculate_delivery_charge(subtotal, pincode=None):
    """Calculate delivery charge based on order amount and location"""
    
    # Free delivery above certain amount
    if subtotal >= Decimal('500'):
        return Decimal('0')
    
    # Default delivery charge
    base_charge = Decimal('50')
    
    # Location-based charges (if pincode provided)
    if pincode:
        try:
            zone = DeliveryZone.objects.filter(
                pincode_start__lte=pincode,
                pincode_end__gte=pincode,
                is_serviceable=True
            ).first()
            
            if zone:
                return zone.delivery_charge if subtotal < Decimal('500') else Decimal('0')
        except:
            pass
    
    return base_charge

def calculate_tax(subtotal):
    """Calculate tax amount"""
    # 18% GST for medical products
    return (subtotal * Decimal('18')) / Decimal('100')

@transaction.atomic
def create_order_from_cart(cart, user, form_data):
    """Create order from cart items"""
    
    # Get address details
    address = form_data['address']
    address_data = {
        'name': address.name,
        'address_line_1': address.address_line_1,
        'address_line_2': address.address_line_2,
        'city': address.city,
        'state': address.state,
        'pincode': address.pincode,
        'landmark': address.landmark,
    }
    
    # Calculate pricing
    subtotal = cart.subtotal
    delivery_charge = calculate_delivery_charge(subtotal, address.pincode)
    tax_amount = Decimal('0')  # Implement if needed
    discount_amount = Decimal('0')
    
    # Apply coupon if any
    from django.core.cache import cache
    session_key = f"applied_coupon_{user.id}" if hasattr(user, 'id') else None
    
    # Calculate total
    total_amount = subtotal + delivery_charge + tax_amount - discount_amount
    
    # Check if prescription required
    prescription_required = any(
        item.product.prescription_required == 'RX' 
        for item in cart.items.all()
    )
    
    # Handle prescription image
    prescription_image = ''
    if form_data.get('prescription_image'):
        image_file = form_data['prescription_image']
        image_data = image_file.read()
        prescription_image = base64.b64encode(image_data).decode('utf-8')
    
    # Create order
    order = Order.objects.create(
        user=user,
        subtotal=subtotal,
        tax_amount=tax_amount,
        delivery_charge=delivery_charge,
        discount_amount=discount_amount,
        total_amount=total_amount,
        payment_method=form_data['payment_method'],
        delivery_address=address_data,
        delivery_phone=user.phone_number,
        notes=form_data.get('notes', ''),
        prescription_required=prescription_required,
        prescription_image=prescription_image,
        estimated_delivery=timezone.now() + timezone.timedelta(days=3)
    )
    
    # Create order items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            price=cart_item.price,
            total_price=cart_item.total_price
        )
        
        # Update stock
        if cart_item.product.track_inventory:
            cart_item.product.stock_quantity -= cart_item.quantity
            cart_item.product.save()
    
    # Create initial status history
    OrderStatusHistory.objects.create(
        order=order,
        status='PENDING',
        notes='Order placed successfully',
        changed_by=user
    )
    
    return order

def get_order_status_display(status):
    """Get user-friendly status display"""
    status_map = {
        'PENDING': 'Order Placed',
        'CONFIRMED': 'Order Confirmed',
        'PROCESSING': 'Preparing Order',
        'SHIPPED': 'Shipped',
        'OUT_FOR_DELIVERY': 'Out for Delivery',
        'DELIVERED': 'Delivered',
        'CANCELLED': 'Cancelled',
        'RETURNED': 'Returned',
        'REFUNDED': 'Refunded',
    }
    return status_map.get(status, status)

def get_next_status(current_status):
    """Get next possible status"""
    status_flow = {
        'PENDING': 'CONFIRMED',
        'CONFIRMED': 'PROCESSING',
        'PROCESSING': 'SHIPPED',
        'SHIPPED': 'OUT_FOR_DELIVERY',
        'OUT_FOR_DELIVERY': 'DELIVERED',
    }
    return status_flow.get(current_status)
