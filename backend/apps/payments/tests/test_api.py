from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import status

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.strategies.base import PaymentInitResult
from apps.test_helpers import (
    auth_client,
    make_order_with_item,
    make_payment,
    make_product,
    make_user,
)

# Force mock providers regardless of local .env credentials.
MOCK_PAYMENT_SETTINGS = {
    "STRIPE_SECRET_KEY": "",
    "STRIPE_WEBHOOK_SECRET": "",
    "BKASH_APP_KEY": "",
    "BKASH_APP_SECRET": "",
    "BKASH_USERNAME": "",
    "BKASH_PASSWORD": "",
    "BKASH_WEBHOOK_SECRET": "",
}


@override_settings(**MOCK_PAYMENT_SETTINGS)
class PaymentAPITests(TestCase):
    def setUp(self):
        self.user = make_user(email="payer@example.com")
        self.other = make_user(email="otherpayer@example.com")
        self.product = make_product(price="20.00", stock=10, sku="PAY-A-1")
        self.order = make_order_with_item(self.user, self.product, quantity=1)
        self.client = auth_client(self.user)

    def test_checkout_stripe_mock(self):
        response = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "stripe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["provider"], "stripe")
        self.assertEqual(response.data["status"], "pending")
        self.assertTrue(response.data["mock"])
        self.assertTrue(str(response.data["transaction_id"]).startswith("pi_mock_"))
        self.assertIn("client_secret", response.data)
        self.assertTrue(
            Payment.objects.filter(
                order=self.order, transaction_id=response.data["transaction_id"]
            ).exists()
        )

    def test_checkout_bkash_mock(self):
        response = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "bkash"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["provider"], "bkash")
        self.assertTrue(response.data["mock"])
        self.assertTrue(str(response.data["transaction_id"]).startswith("bkash_mock_"))

    def test_checkout_requires_auth(self):
        from rest_framework.test import APIClient

        response = APIClient().post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "stripe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkout_rejects_other_users_order(self):
        other_order = make_order_with_item(self.other, self.product)
        response = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(other_order.id), "provider": "stripe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_rejects_paid_order(self):
        self.order.mark_paid()
        response = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "stripe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_reopens_canceled_order(self):
        self.order.mark_canceled()
        response = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "stripe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_confirm_mock_marks_order_paid_and_reduces_stock(self):
        checkout = self.client.post(
            "/api/payments/checkout/",
            {"order_id": str(self.order.id), "provider": "stripe"},
            format="json",
        )
        payment_id = checkout.data["id"]
        response = self.client.post(
            "/api/payments/confirm/",
            {"payment_id": payment_id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 9)

    def test_confirm_by_transaction_id(self):
        payment = make_payment(
            self.order,
            transaction_id="pi_mock_confirm_tx",
            status=Payment.Status.PENDING,
        )
        response = self.client.post(
            "/api/payments/confirm/",
            {"transaction_id": payment.transaction_id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    def test_confirm_callback_cancel_fails_payment_and_cancels_order(self):
        payment = make_payment(self.order, transaction_id="pi_mock_cancel_cb")
        response = self.client.post(
            "/api/payments/confirm/",
            {"payment_id": str(payment.id), "callback_status": "cancel"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "failed")
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.status, Order.Status.CANCELED)

    def test_confirm_is_idempotent_when_already_success(self):
        payment = make_payment(
            self.order,
            transaction_id="pi_mock_already",
            status=Payment.Status.SUCCESS,
        )
        response = self.client.post(
            "/api/payments/confirm/",
            {"payment_id": str(payment.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    def test_list_payments_scoped_to_owner(self):
        make_payment(self.order, transaction_id="tx_mine")
        other_order = make_order_with_item(self.other, self.product)
        make_payment(other_order, transaction_id="tx_theirs")

        response = self.client.get("/api/payments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        txs = {row["transaction_id"] for row in response.data}
        self.assertIn("tx_mine", txs)
        self.assertNotIn("tx_theirs", txs)

    def test_checkout_deletes_payment_when_initiate_fails(self):
        with patch(
            "apps.payments.strategies.stripe_strategy.StripeStrategy.initiate_payment",
            side_effect=ValueError("provider down"),
        ):
            response = self.client.post(
                "/api/payments/checkout/",
                {"order_id": str(self.order.id), "provider": "stripe"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 0)

    def test_checkout_marks_paid_when_initiate_returns_success(self):
        with patch(
            "apps.payments.strategies.stripe_strategy.StripeStrategy.initiate_payment",
            return_value=PaymentInitResult(
                transaction_id="pi_instant_success",
                status="success",
                raw_response={"ok": True},
                mock=True,
            ),
        ):
            response = self.client.post(
                "/api/payments/checkout/",
                {"order_id": str(self.order.id), "provider": "stripe"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(Decimal(response.data["amount"]), Decimal("20.00"))
