from decimal import Decimal
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from apps.core.models import DeliveryZone
from .models import Order, OrderItem, OrderStatusHistory, CouponUsage


def calculate_delivery_charge(subtotal, pincode=None):
    """Calculate delivery charge based on order amount and location"""

    # Free delivery above certain amount
    if subtotal >= Decimal("500"):
        return Decimal("0")

    # Default delivery charge
    base_charge = Decimal("50")

    # Location-based charges (if pincode provided)
    if pincode:
        try:
            zone = DeliveryZone.objects.filter(
                pincode_start__lte=pincode,
                pincode_end__gte=pincode,
                is_serviceable=True,
            ).first()

            if zone:
                return (
                    zone.delivery_charge if subtotal < Decimal("500") else Decimal("0")
                )
        except:
            pass

    return base_charge


def calculate_tax(subtotal):
    """Calculate tax amount"""
    # 18% GST for medical products
    return (subtotal * Decimal("18")) / Decimal("100")


def get_applied_coupon_data(request, subtotal):
    """Return validated coupon session data for the current request."""
    applied_coupon_session = request.session.get("applied_coupon")
    if not applied_coupon_session:
        return {
            "coupon": None,
            "discount_amount": Decimal("0.00"),
            "delivery_charge_override": None,
        }

    from .models import Coupon

    try:
        coupon = Coupon.objects.get(code=applied_coupon_session["code"])
    except Coupon.DoesNotExist:
        request.session.pop("applied_coupon", None)
        return {
            "coupon": None,
            "discount_amount": Decimal("0.00"),
            "delivery_charge_override": None,
        }

    is_valid, _ = coupon.is_valid_for_user(request.user, subtotal)
    if not is_valid:
        request.session.pop("applied_coupon", None)
        return {
            "coupon": None,
            "discount_amount": Decimal("0.00"),
            "delivery_charge_override": None,
        }

    discount_amount = Decimal(str(applied_coupon_session.get("discount", 0)))
    delivery_charge_override = None
    if applied_coupon_session.get("type") == "FREE_DELIVERY":
        delivery_charge_override = Decimal("0.00")

    return {
        "coupon": coupon,
        "discount_amount": discount_amount,
        "delivery_charge_override": delivery_charge_override,
    }


def restore_order_stock(order):
    """Restore reserved stock back to products for a failed or cancelled order."""
    for item in order.items.select_related("product").all():
        if item.product.track_inventory:
            item.product.stock_quantity += item.quantity
            item.product.save(update_fields=["stock_quantity", "updated_at"])


def mark_order_payment_failed(order, notes="Payment failed or was cancelled"):
    """Mark an online order as failed and restore stock once."""
    if order.payment_status in {"FAILED", "PAID"}:
        return order

    restore_order_stock(order)
    order.payment_status = "FAILED"
    order.save(update_fields=["payment_status", "updated_at"])
    OrderStatusHistory.objects.create(
        order=order,
        status=order.status,
        notes=notes,
    )
    return order


def finalize_online_order(
    order,
    payment_id="",
    coupon=None,
    discount_amount=Decimal("0.00"),
    clear_user_cart=True,
):
    """Finalize an online order after Razorpay confirms payment."""
    if order.payment_status != "PAID":
        order.payment_status = "PAID"
        order.status = "CONFIRMED"
        if payment_id and not order.payment_id:
            order.payment_id = payment_id
        elif payment_id:
            order.payment_id = payment_id
        order.save(
            update_fields=["payment_status", "status", "payment_id", "updated_at"]
        )

        OrderStatusHistory.objects.create(
            order=order,
            status="CONFIRMED",
            notes="Payment confirmed via Razorpay",
            changed_by=order.user,
        )
    elif payment_id and order.payment_id != payment_id:
        order.payment_id = payment_id
        order.save(update_fields=["payment_id", "updated_at"])

    if coupon and not CouponUsage.objects.filter(coupon=coupon, order=order).exists():
        CouponUsage.objects.create(
            coupon=coupon,
            user=order.user,
            order=order,
            discount_amount=discount_amount,
        )
        coupon.usage_count = F("usage_count") + 1
        coupon.save(update_fields=["usage_count"])
        coupon.refresh_from_db(fields=["usage_count"])

    if clear_user_cart:
        try:
            order.user.cart.clear()
        except Exception:
            pass

    return order


@transaction.atomic
def create_order_from_cart(
    cart,
    user,
    form_data,
    discount_amount=Decimal("0.00"),
    delivery_charge=None,
    coupon_code="",
):
    """Create order from cart items"""

    # Get address details
    address = form_data["address"]
    address_data = {
        "name": address.name,
        "address_line_1": address.address_line_1,
        "address_line_2": address.address_line_2 or "",
        "city": address.city,
        "state": address.state,
        "pincode": address.pincode,
        "landmark": address.landmark or "",
    }

    # Calculate pricing
    subtotal = cart.subtotal
    if delivery_charge is None:
        delivery_charge = calculate_delivery_charge(subtotal, address.pincode)
    tax_amount = Decimal("0")

    # Calculate total
    total_amount = subtotal + delivery_charge + tax_amount - discount_amount

    # Check if prescription required
    prescription_required = any(
        item.product.prescription_required == "RX" for item in cart.items.all()
    )

    # Handle prescription image
    prescription_image = None
    if form_data.get("prescription_image"):
        image_file = form_data["prescription_image"]
        image_file.seek(0)
        prescription_image = ContentFile(
            image_file.read(), name=image_file.name
        )

    # Create order
    order = Order.objects.create(
        user=user,
        subtotal=subtotal,
        tax_amount=tax_amount,
        delivery_charge=delivery_charge,
        discount_amount=discount_amount,
        total_amount=total_amount,
        applied_coupon_code=coupon_code,
        payment_method=form_data["payment_method"],
        delivery_address=address_data,
        delivery_phone=user.phone_number,
        notes=form_data.get("notes", ""),
        prescription_required=prescription_required,
        estimated_delivery=timezone.now() + timezone.timedelta(days=3),
    )

    if prescription_image:
        order.prescription_image.save(
            prescription_image.name, prescription_image, save=True
        )

    # Create order items
    for cart_item in cart.items.all():
        product = cart_item.product.__class__.objects.select_for_update().get(
            pk=cart_item.product_id
        )
        if product.track_inventory and product.stock_quantity < cart_item.quantity:
            raise ValueError(f"Insufficient stock for {product.name}")

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=cart_item.quantity,
            price=cart_item.price,
            total_price=cart_item.total_price,
        )

        # Update stock
        if product.track_inventory:
            product.stock_quantity -= cart_item.quantity
            product.save(update_fields=["stock_quantity", "updated_at"])

    # Create initial status history
    OrderStatusHistory.objects.create(
        order=order,
        status="PENDING",
        notes="Order placed successfully",
        changed_by=user,
    )

    return order


def get_order_status_display(status):
    """Get user-friendly status display"""
    status_map = {
        "PENDING": "Order Placed",
        "CONFIRMED": "Order Confirmed",
        "PROCESSING": "Preparing Order",
        "SHIPPED": "Shipped",
        "OUT_FOR_DELIVERY": "Out for Delivery",
        "DELIVERED": "Delivered",
        "CANCELLED": "Cancelled",
        "RETURNED": "Returned",
        "REFUNDED": "Refunded",
    }
    return status_map.get(status, status)


def get_next_status(current_status):
    """Get next possible status"""
    status_flow = {
        "PENDING": "CONFIRMED",
        "CONFIRMED": "PROCESSING",
        "PROCESSING": "SHIPPED",
        "SHIPPED": "OUT_FOR_DELIVERY",
        "OUT_FOR_DELIVERY": "DELIVERED",
    }
    return status_flow.get(current_status)
