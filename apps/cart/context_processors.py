def cart_counts(request):
    """Expose cart item count in all templates (session + authenticated)."""
    try:
        from .utils import get_cart_context

        return {"cart_items_count": get_cart_context(request)["cart_items_count"]}
    except Exception:
        return {"cart_items_count": 0}
