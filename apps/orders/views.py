import json
import logging
import razorpay
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from apps.cart.models import Cart
from apps.cart.utils import get_or_create_cart
from apps.accounts.models import Address
from .models import (
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    OrderStatusHistory,
    RazorpayWebhookEvent,
)
from .forms import CheckoutForm, CouponForm
from .utils import (
    calculate_delivery_charge,
    create_order_from_cart,
    finalize_online_order,
    get_applied_coupon_data,
    mark_order_payment_failed,
)

logger = logging.getLogger(__name__)


def get_selected_checkout_address(addresses, selected_address_id=None):
    """Return the selected/default checkout address, falling back to the first one."""
    if selected_address_id:
        selected_address = addresses.filter(id=selected_address_id).first()
        if selected_address:
            return selected_address

    return addresses.filter(is_default=True).first() or addresses.first()


def get_coupon_for_order(order):
    """Return the coupon associated with an order, if any."""
    if not order.applied_coupon_code:
        return None
    return Coupon.objects.filter(code=order.applied_coupon_code).first()


class OrderListView(LoginRequiredMixin, ListView):
    """User's order list"""

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("user")


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view"""

    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items__product__manufacturer", "status_history"
        )


@login_required
def checkout_view(request):
    """Checkout page"""
    cart = get_or_create_cart(request)

    if not cart.items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart:cart")

    addresses = Address.objects.filter(user=request.user)
    subtotal = cart.subtotal

    selected_address = get_selected_checkout_address(
        addresses,
        request.POST.get("address") if request.method == "POST" else None,
    )
    pincode = selected_address.pincode if selected_address else None
    delivery_charge = calculate_delivery_charge(subtotal, pincode)

    coupon_data = get_applied_coupon_data(request, subtotal)
    discount_amount = coupon_data["discount_amount"]
    if coupon_data["delivery_charge_override"] is not None:
        delivery_charge = coupon_data["delivery_charge_override"]
    total = subtotal + delivery_charge - discount_amount

    if request.method == "POST":
        form = CheckoutForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            payment_method = form.cleaned_data["payment_method"]
            if payment_method == "ONLINE":
                messages.error(request, "Please use the Pay Online button.")
            else:
                try:
                    with transaction.atomic():
                        coupon_data = get_applied_coupon_data(request, subtotal)
                        coupon_discount = coupon_data["discount_amount"]
                        coupon_obj = coupon_data["coupon"]
                        if coupon_data["delivery_charge_override"] is not None:
                            delivery_charge = coupon_data["delivery_charge_override"]

                        order = create_order_from_cart(
                            cart=cart,
                            user=request.user,
                            form_data=form.cleaned_data,
                            discount_amount=coupon_discount,
                            delivery_charge=delivery_charge,
                            coupon_code=coupon_obj.code if coupon_obj else "",
                        )

                        if coupon_obj:
                            CouponUsage.objects.create(
                                coupon=coupon_obj,
                                user=request.user,
                                order=order,
                                discount_amount=coupon_discount,
                            )
                            coupon_obj.usage_count += 1
                            coupon_obj.save(update_fields=["usage_count"])
                            request.session.pop("applied_coupon", None)

                        cart.clear()
                        messages.success(
                            request, f"Order {order.order_number} placed successfully!"
                        )
                        return redirect(
                            "orders:order_detail", order_number=order.order_number
                        )
                except Exception as e:
                    messages.error(request, f"Error placing order: {e}")
        else:
            initial_data = {}
            if selected_address:
                initial_data["address"] = selected_address.id
            form = CheckoutForm(initial=initial_data, user=request.user)
    else:
        initial_data = {}
        if selected_address:
            initial_data["address"] = selected_address.id
        form = CheckoutForm(initial=initial_data, user=request.user)

    context = {
        "form": form,
        "cart": cart,
        "cart_items": cart.items.select_related(
            "product", "product__manufacturer"
        ).all(),
        "addresses": addresses,
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "discount_amount": discount_amount,
        "total": total,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "selected_address_id": selected_address.id if selected_address else None,
    }

    return render(request, "orders/checkout.html", context)


@login_required
@require_POST
def apply_coupon(request):
    """Apply coupon code"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get("coupon_code", "").strip().upper()

        if not coupon_code:
            return JsonResponse(
                {"success": False, "message": "Please enter a coupon code"}
            )

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid coupon code"})

        # Calculate cart total
        cart = get_or_create_cart(request)
        subtotal = cart.subtotal

        # Validate coupon
        is_valid, message = coupon.is_valid_for_user(request.user, subtotal)
        if not is_valid:
            return JsonResponse({"success": False, "message": message})

        # Calculate discount
        discount = coupon.calculate_discount(subtotal)
        delivery_charge = calculate_delivery_charge(subtotal)

        if coupon.coupon_type == "FREE_DELIVERY":
            delivery_charge = 0
            discount = calculate_delivery_charge(
                subtotal
            )  # Show delivery charge as discount

        total = subtotal + delivery_charge - discount

        # Store coupon in session
        request.session["applied_coupon"] = {
            "code": coupon.code,
            "discount": float(discount),
            "type": coupon.coupon_type,
        }

        return JsonResponse(
            {
                "success": True,
                "message": f"Coupon {coupon.code} applied successfully!",
                "discount": float(discount),
                "delivery_charge": float(delivery_charge),
                "total": float(total),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": "Error applying coupon"})


@login_required
@require_POST
def remove_coupon(request):
    """Remove applied coupon"""
    request.session.pop("applied_coupon", None)

    cart = get_or_create_cart(request)
    subtotal = cart.subtotal
    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge

    return JsonResponse(
        {
            "success": True,
            "message": "Coupon removed",
            "discount": 0,
            "delivery_charge": float(delivery_charge),
            "total": float(total),
        }
    )


@login_required
@require_POST
def cancel_order(request, order_number):
    """Cancel an order"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if not order.can_be_cancelled:
        return JsonResponse(
            {"success": False, "message": "This order cannot be cancelled"}
        )

    try:
        with transaction.atomic():
            # Update order status
            order.status = "CANCELLED"
            order.save()

            # Add status history
            OrderStatusHistory.objects.create(
                order=order,
                status="CANCELLED",
                notes="Cancelled by customer",
                changed_by=request.user,
            )

            # Restore stock
            for item in order.items.all():
                if item.product.track_inventory:
                    item.product.stock_quantity += item.quantity
                    item.product.save()

        return JsonResponse(
            {"success": True, "message": "Order cancelled successfully"}
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": "Error cancelling order"})


def order_tracking(request, order_number):
    """Public order tracking page"""
    try:
        order = Order.objects.get(order_number=order_number)

        # If user is logged in, verify ownership
        if request.user.is_authenticated and order.user != request.user:
            messages.error(request, "Order not found")
            return redirect("orders:order_list")

        context = {"order": order, "status_history": order.status_history.all()}

        return render(request, "orders/order_tracking.html", context)

    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect("core:home")


@login_required
@require_POST
def initiate_razorpay_order(request):
    """Create Razorpay order and a pending Django order for online payment."""
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"})

    form_data = request.POST.copy()
    if not form_data.get("address"):
        selected_address = get_selected_checkout_address(
            Address.objects.filter(user=request.user)
        )
        if selected_address:
            form_data["address"] = selected_address.id

    form = CheckoutForm(form_data, request.FILES, user=request.user)
    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "message": "Please fix form errors",
                "errors": form.errors,
            }
        )

    try:
        with transaction.atomic():
            subtotal = cart.subtotal
            delivery_charge = calculate_delivery_charge(subtotal)
            coupon_data = get_applied_coupon_data(request, subtotal)
            coupon_discount = coupon_data["discount_amount"]
            coupon_obj = coupon_data["coupon"]
            if coupon_data["delivery_charge_override"] is not None:
                delivery_charge = coupon_data["delivery_charge_override"]

            total_amount = subtotal + delivery_charge - coupon_discount

            order = create_order_from_cart(
                cart=cart,
                user=request.user,
                form_data=form.cleaned_data,
                discount_amount=coupon_discount,
                delivery_charge=delivery_charge,
                coupon_code=coupon_obj.code if coupon_obj else "",
            )

            # Create Razorpay order
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            razorpay_order = client.order.create(
                {
                    "amount": int(total_amount * 100),
                    "currency": "INR",
                    "receipt": order.order_number,
                    "payment_capture": 1,
                }
            )

            order.razorpay_order_id = razorpay_order["id"]
            order.save(update_fields=["razorpay_order_id"])

            return JsonResponse(
                {
                    "success": True,
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": int(total_amount * 100),
                    "currency": "INR",
                    "order_number": order.order_number,
                    "key_id": settings.RAZORPAY_KEY_ID,
                    "prefill": {
                        "name": request.user.get_full_name() or request.user.email,
                        "email": request.user.email,
                        "contact": getattr(request.user, "phone_number", ""),
                    },
                }
            )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
@require_POST
def verify_razorpay_payment(request):
    """Verify Razorpay signature and confirm order."""
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_signature = data.get("razorpay_signature")
        order_number = data.get("order_number")

        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.razorpay_order_id and order.razorpay_order_id != razorpay_order_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Order mismatch during payment verification.",
                },
                status=400,
            )

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except razorpay.errors.SignatureVerificationError:
            mark_order_payment_failed(
                order, notes="Payment signature verification failed"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payment verification failed. Contact support.",
                }
            )

        with transaction.atomic():
            coupon = get_coupon_for_order(order)
            finalize_online_order(
                order=order,
                payment_id=razorpay_payment_id,
                coupon=coupon,
                discount_amount=order.discount_amount,
            )
            request.session.pop("applied_coupon", None)

        return JsonResponse(
            {
                "success": True,
                "message": "Payment successful!",
                "redirect_url": reverse(
                    "orders:order_detail", kwargs={"order_number": order.order_number}
                ),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
@require_POST
def razorpay_payment_failed(request):
    """Mark order payment as FAILED when Razorpay dismissal occurs."""
    try:
        data = json.loads(request.body)
        order_number = data.get("order_number")
        if order_number:
            order = Order.objects.filter(
                order_number=order_number, user=request.user
            ).first()
            if order and order.payment_status == "PENDING":
                mark_order_payment_failed(
                    order, notes="Payment was cancelled before completion"
                )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
@require_POST
def request_return(request, order_number):
    """Submit a return request for a delivered order."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status != "DELIVERED":
        return JsonResponse(
            {"success": False, "message": "Only delivered orders can be returned."}
        )

    reason = request.POST.get("reason", "").strip()
    if not reason:
        return JsonResponse(
            {"success": False, "message": "Please provide a reason for return."}
        )

    from .models import OrderRefund

    OrderRefund.objects.create(
        order=order,
        refund_type="FULL",
        amount=order.total_amount,
        reason=reason,
        status="REQUESTED",
    )
    order.status = "RETURNED"
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(
        order=order,
        status="RETURNED",
        notes=f"Return requested: {reason}",
        changed_by=request.user,
    )
    return JsonResponse(
        {"success": True, "message": "Return request submitted successfully."}
    )


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks for captured and failed payments."""
    if request.method != "POST":
        return JsonResponse({"status": "ignored"}, status=405)

    webhook_event = None
    try:
        payload = request.body.decode("utf-8")
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        if not webhook_secret and not settings.DEBUG:
            return JsonResponse({"status": "webhook secret not configured"}, status=500)

        # Verify webhook signature if secret is configured
        if webhook_secret:
            razorpay_webhook_signature = request.headers.get("X-Razorpay-Signature", "")
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            try:
                client.utility.verify_webhook_signature(
                    payload, razorpay_webhook_signature, webhook_secret
                )
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({"status": "invalid signature"}, status=400)

        event = json.loads(payload)
        event_type = event.get("event")
        event_id = request.headers.get("X-Razorpay-Event-Id", "").strip()

        if not event_id:
            return JsonResponse({"status": "missing event id"}, status=400)

        if not event_type:
            return JsonResponse({"status": "missing event type"}, status=400)

        try:
            webhook_event = RazorpayWebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                payload=event,
            )
        except IntegrityError:
            return JsonResponse({"status": "duplicate ignored"})

        payload_data = event.get("payload", {})

        if event_type in {"payment.captured", "order.paid"}:
            payment = payload_data.get("payment", {}).get("entity", {})
            order_entity = payload_data.get("order", {}).get("entity", {})
            razorpay_order_id = payment.get("order_id") or order_entity.get("id")
            order_number = order_entity.get("receipt")

            order = None
            if razorpay_order_id:
                order = Order.objects.filter(
                    razorpay_order_id=razorpay_order_id
                ).first()
            if not order and order_number:
                order = Order.objects.filter(order_number=order_number).first()

            if order:
                coupon = get_coupon_for_order(order)
                finalize_online_order(
                    order=order,
                    payment_id=payment.get("id", ""),
                    coupon=coupon,
                    discount_amount=order.discount_amount,
                )

        elif event_type == "payment.failed":
            payment = event.get("payload", {}).get("payment", {}).get("entity", {})
            razorpay_order_id = payment.get("order_id")
            order = None
            if razorpay_order_id:
                order = Order.objects.filter(
                    razorpay_order_id=razorpay_order_id
                ).first()
            if not order:
                order_number = payment.get("receipt")
                if order_number:
                    order = Order.objects.filter(order_number=order_number).first()
            if order and order.payment_status == "PENDING":
                mark_order_payment_failed(
                    order, notes="Payment failed via Razorpay webhook"
                )

        if webhook_event:
            webhook_event.mark_processed(notes="Event handled successfully")

        return JsonResponse({"status": "processed"})

    except Exception as e:
        if webhook_event:
            webhook_event.mark_failed(str(e))
        logger.exception("Razorpay webhook processing failed")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
