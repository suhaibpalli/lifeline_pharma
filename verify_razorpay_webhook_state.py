import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharma_ecommerce.settings")

import django

django.setup()

from apps.cart.models import Cart
from apps.orders.models import Order, RazorpayWebhookEvent


def main():
    latest_order = (
        Order.objects.filter(payment_method="ONLINE")
        .select_related("user")
        .order_by("-created_at")
        .first()
    )

    if not latest_order:
        print("No online orders found.")
        return

    cart = Cart.objects.filter(user=latest_order.user).first()
    cart_items = cart.items.count() if cart else 0

    print("Latest online order")
    print(f"  order_number: {latest_order.order_number}")
    print(f"  user: {latest_order.user.email}")
    print(f"  status: {latest_order.status}")
    print(f"  payment_status: {latest_order.payment_status}")
    print(f"  payment_method: {latest_order.payment_method}")
    print(f"  payment_id: {latest_order.payment_id or '<empty>'}")
    print(f"  razorpay_order_id: {latest_order.razorpay_order_id or '<empty>'}")
    print(f"  created_at: {latest_order.created_at}")
    print(f"  updated_at: {latest_order.updated_at}")
    print(f"  items_count: {latest_order.items.count()}")
    print(f"  user_cart_items_after_payment: {cart_items}")
    print(
        f"  coupon_usage_count: {latest_order.couponusage_set.count() if hasattr(latest_order, 'couponusage_set') else 0}"
    )

    print("")
    print("Recent webhook events")
    recent_events = RazorpayWebhookEvent.objects.order_by("-created_at")[:10]
    if not recent_events:
        print("  No webhook events found.")
    else:
        for event in recent_events:
            print(
                "  "
                f"event_id={event.event_id} "
                f"type={event.event_type} "
                f"status={event.processing_status} "
                f"processed_at={event.processed_at} "
                f"created_at={event.created_at}"
            )

    processed_count = RazorpayWebhookEvent.objects.filter(
        processing_status="PROCESSED"
    ).count()
    failed_count = RazorpayWebhookEvent.objects.filter(
        processing_status="FAILED"
    ).count()

    print("")
    print("Summary")
    print(f"  processed_webhook_events: {processed_count}")
    print(f"  failed_webhook_events: {failed_count}")
    print(
        "  verification_result: "
        + (
            "PASS"
            if latest_order.payment_status == "PAID"
            and latest_order.status == "CONFIRMED"
            and cart_items == 0
            and failed_count == 0
            else "CHECK_MANUALLY"
        )
    )


if __name__ == "__main__":
    main()
