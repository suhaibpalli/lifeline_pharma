from .models import Cart, CartItem
from apps.products.models import Product

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def merge_session_cart_to_user_cart(request):
    """Merge session cart with user cart after login"""
    if not request.user.is_authenticated:
        return
    
    session_key = request.session.session_key
    if not session_key:
        return
    
    try:
        # Get session cart
        session_cart = Cart.objects.get(session_key=session_key)
        
        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Merge items
        for session_item in session_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=session_item.product,
                defaults={
                    'quantity': session_item.quantity,
                    'price': session_item.price
                }
            )
            
            if not created:
                # Item already exists, update quantity
                user_item.quantity += session_item.quantity
                user_item.save()
        
        # Delete session cart
        session_cart.delete()
        
    except Cart.DoesNotExist:
        pass

def get_cart_context(request):
    """Get cart context for templates"""
    cart = get_or_create_cart(request)
    return {
        'cart': cart,
        'cart_items_count': cart.total_items,
        'cart_subtotal': cart.subtotal,
    }
