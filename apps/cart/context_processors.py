def cart_counts(request):
    """Expose cart item count in all templates (session + authenticated)."""
    try:
        from .models import Cart

        # Browsing the storefront must not create a cart/session for every bot
        # or first-time visitor. Creation belongs to the explicit cart actions.
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        elif request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key).first()
        else:
            cart = None
        return {"cart_items_count": cart.total_items if cart else 0}
    except Exception:
        return {"cart_items_count": 0}
