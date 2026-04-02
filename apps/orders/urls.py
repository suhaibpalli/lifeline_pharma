from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # Order management
    path("", views.OrderListView.as_view(), name="order_list"),
    # Checkout (must be before order_number pattern)
    path("checkout/", views.checkout_view, name="checkout"),
    # Coupon management (must be before order_number pattern)
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("remove-coupon/", views.remove_coupon, name="remove_coupon"),
    # Order detail (must be after specific paths)
    path("<str:order_number>/", views.OrderDetailView.as_view(), name="order_detail"),
    # Order actions
    path("<str:order_number>/cancel/", views.cancel_order, name="cancel_order"),
    path("<str:order_number>/return/", views.request_return, name="request_return"),
    # Public tracking
    path("track/<str:order_number>/", views.order_tracking, name="order_tracking"),
    # Razorpay payment routes
    path(
        "payment/initiate/",
        views.initiate_razorpay_order,
        name="initiate_razorpay_order",
    ),
    path(
        "payment/verify/",
        views.verify_razorpay_payment,
        name="verify_razorpay_payment",
    ),
    path(
        "payment/failed/",
        views.razorpay_payment_failed,
        name="razorpay_payment_failed",
    ),
    # Razorpay webhook
    path("webhook/", views.razorpay_webhook, name="razorpay_webhook"),
]
