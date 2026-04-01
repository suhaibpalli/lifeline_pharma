import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Address
from apps.cart.models import Cart, CartItem
from apps.orders.models import Coupon, CouponUsage, Order, OrderItem
from apps.products.models import Category, Manufacturer, Product

User = get_user_model()


class RazorpayFlowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="buyer@example.com",
            password="pass12345",
            phone_number="9876543210",
        )
        self.address = Address.objects.create(
            user=self.user,
            name="Home",
            address_line_1="No 1 Test Street",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600092",
            is_default=True,
        )
        self.category = Category.objects.create(name="Medicines")
        self.manufacturer = Manufacturer.objects.create(name="Acme Pharma")
        self.product = Product.objects.create(
            name="Pain Relief",
            category=self.category,
            manufacturer=self.manufacturer,
            description="Pain relief tablets",
            mrp_price=Decimal("150.00"),
            patient_price=Decimal("120.00"),
            pharmacy_price=Decimal("100.00"),
            stock_quantity=10,
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.patient_price,
        )
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            name="Save 10",
            coupon_type="FIXED",
            value=Decimal("10.00"),
            minimum_amount=Decimal("50.00"),
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )
        self.client.force_login(self.user)

    def set_coupon_session(self):
        session = self.client.session
        session["applied_coupon"] = {
            "code": self.coupon.code,
            "discount": 10.0,
            "type": self.coupon.coupon_type,
        }
        session.save()

    def create_pending_online_order(self, coupon_code=""):
        order = Order.objects.create(
            user=self.user,
            subtotal=Decimal("240.00"),
            delivery_charge=Decimal("50.00"),
            discount_amount=Decimal("10.00") if coupon_code else Decimal("0.00"),
            total_amount=Decimal("280.00") if coupon_code else Decimal("290.00"),
            applied_coupon_code=coupon_code,
            payment_method="ONLINE",
            delivery_address={
                "name": self.address.name,
                "address_line_1": self.address.address_line_1,
                "address_line_2": "",
                "city": self.address.city,
                "state": self.address.state,
                "pincode": self.address.pincode,
                "landmark": "",
            },
            delivery_phone=self.user.phone_number,
            razorpay_order_id="order_razorpay_123",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.patient_price,
            total_price=Decimal("240.00"),
        )
        self.product.stock_quantity = 8
        self.product.save(update_fields=["stock_quantity", "updated_at"])
        return order

    def test_checkout_page_renders_with_payment_urls(self):
        response = self.client.get(reverse("orders:checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("orders:initiate_razorpay_order"))
        self.assertContains(response, reverse("orders:verify_razorpay_payment"))
        self.assertContains(response, reverse("orders:razorpay_payment_failed"))

    @patch("apps.orders.views.razorpay.Client")
    def test_initiate_razorpay_order_creates_pending_order_and_stores_coupon_code(
        self, mock_client
    ):
        self.set_coupon_session()
        mock_client.return_value.order.create.return_value = {"id": "order_test_123"}

        response = self.client.post(
            reverse("orders:initiate_razorpay_order"),
            {
                "address": self.address.id,
                "payment_method": "ONLINE",
                "notes": "Call on arrival",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        order = Order.objects.get(order_number=data["order_number"])
        self.product.refresh_from_db()

        self.assertEqual(order.razorpay_order_id, "order_test_123")
        self.assertEqual(order.applied_coupon_code, "SAVE10")
        self.assertEqual(self.product.stock_quantity, 8)

    def test_failed_payment_restores_stock_once(self):
        order = self.create_pending_online_order()

        response = self.client.post(
            reverse("orders:razorpay_payment_failed"),
            data=json.dumps({"order_number": order.order_number}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, "FAILED")
        self.assertEqual(self.product.stock_quantity, 10)

        self.client.post(
            reverse("orders:razorpay_payment_failed"),
            data=json.dumps({"order_number": order.order_number}),
            content_type="application/json",
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    @patch("apps.orders.views.razorpay.Client")
    def test_verify_razorpay_payment_marks_paid_and_clears_cart(self, mock_client):
        order = self.create_pending_online_order(coupon_code=self.coupon.code)
        self.set_coupon_session()
        mock_client.return_value.utility.verify_payment_signature.return_value = None

        response = self.client.post(
            reverse("orders:verify_razorpay_payment"),
            data=json.dumps(
                {
                    "razorpay_payment_id": "pay_123",
                    "razorpay_order_id": order.razorpay_order_id,
                    "razorpay_signature": "sig_123",
                    "order_number": order.order_number,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(order.payment_status, "PAID")
        self.assertEqual(order.status, "CONFIRMED")
        self.assertEqual(order.payment_id, "pay_123")
        self.assertEqual(self.cart.items.count(), 0)
        self.assertTrue(
            CouponUsage.objects.filter(order=order, coupon=self.coupon).exists()
        )

    @override_settings(DEBUG=True)
    def test_payment_captured_webhook_finalizes_late_payment(self):
        order = self.create_pending_online_order(coupon_code=self.coupon.code)

        response = self.client.post(
            reverse("orders:razorpay_webhook"),
            data=json.dumps(
                {
                    "event": "payment.captured",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": "pay_late_123",
                                "order_id": order.razorpay_order_id,
                            }
                        }
                    },
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(order.payment_status, "PAID")
        self.assertEqual(order.payment_id, "pay_late_123")
        self.assertEqual(self.cart.items.count(), 0)
        self.assertTrue(
            CouponUsage.objects.filter(order=order, coupon=self.coupon).exists()
        )

    @override_settings(DEBUG=False)
    def test_webhook_requires_secret_outside_debug(self):
        response = self.client.post(
            reverse("orders:razorpay_webhook"),
            data=json.dumps({"event": "payment.captured", "payload": {}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
