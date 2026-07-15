import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.strategies.base import PaymentInitResult
from apps.test_helpers import make_order_with_item, make_payment, make_product, make_user


class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="stripe-wh@example.com")
        self.product = make_product(price="15.00", stock=5, sku="WH-S-1")
        self.order = make_order_with_item(self.user, self.product)
        self.payment = make_payment(
            self.order,
            provider=Payment.Provider.STRIPE,
            transaction_id="pi_webhook_abc",
        )

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_unverified_succeeded_marks_paid(self):
        payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_webhook_abc", "status": "succeeded"}},
        }
        response = self.client.post(
            "/api/payments/webhooks/stripe/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 4)

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_payment_failed_cancels_pending_order(self):
        payload = {
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_webhook_abc"}},
        }
        response = self.client.post(
            "/api/payments/webhooks/stripe/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "failed")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELED)

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_unknown_transaction_is_ignored(self):
        payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_unknown"}},
        }
        response = self.client.post(
            "/api/payments/webhooks/stripe/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "ignored")

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_idempotent_when_already_success(self):
        self.payment.status = Payment.Status.SUCCESS
        self.payment.save(update_fields=["status"])
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=["status"])

        payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_webhook_abc"}},
        }
        response = self.client.post(
            "/api/payments/webhooks/stripe/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret")
    def test_missing_signature_rejected(self):
        response = self.client.post(
            "/api/payments/webhooks/stripe/",
            data={"type": "payment_intent.succeeded"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("signature", response.data["detail"].lower())

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret")
    def test_invalid_signature_rejected(self):
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=__import__("stripe").SignatureVerificationError(
                "bad sig", "sig_header"
            ),
        ):
            response = self.client.post(
                "/api/payments/webhooks/stripe/",
                data=b'{"type":"payment_intent.succeeded"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=bad",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("signature", response.data["detail"].lower())

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret")
    def test_valid_signature_processes_event(self):
        event = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_webhook_abc"}},
        }
        mock_event = MagicMock()
        mock_event.to_dict.return_value = event
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            response = self.client.post(
                "/api/payments/webhooks/stripe/",
                data=json.dumps(event),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=good",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)


BKASH_CONFIGURED = {
    "BKASH_APP_KEY": "app_key",
    "BKASH_APP_SECRET": "app_secret",
    "BKASH_USERNAME": "user",
    "BKASH_PASSWORD": "pass",
    "BKASH_WEBHOOK_SECRET": "",
}


class BkashWebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="bkash-wh@example.com")
        self.product = make_product(price="30.00", stock=8, sku="WH-B-1")
        self.order = make_order_with_item(self.user, self.product)
        self.payment = make_payment(
            self.order,
            provider=Payment.Provider.BKASH,
            transaction_id="TR0011BKASH",
        )

    @override_settings(**BKASH_CONFIGURED)
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._grant_token", return_value="token")
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._query")
    def test_success_via_provider_query(self, mock_query, _mock_token):
        mock_query.return_value = {
            "paymentID": "TR0011BKASH",
            "transactionStatus": "Completed",
        }
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"paymentID": "TR0011BKASH", "transactionStatus": "Failed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Payload status is ignored; Query API decides.
        self.assertEqual(response.data["status"], "success")
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 7)

    @override_settings(**BKASH_CONFIGURED)
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._grant_token", return_value="token")
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._query")
    def test_failed_via_provider_query(self, mock_query, _mock_token):
        mock_query.return_value = {
            "paymentID": "TR0011BKASH",
            "transactionStatus": "Failed",
        }
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"paymentID": "TR0011BKASH"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "failed")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELED)

    @override_settings(**BKASH_CONFIGURED)
    def test_missing_payment_id_rejected(self):
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"transactionStatus": "Completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mock_transaction_rejected(self):
        mock_payment = make_payment(
            self.order,
            provider=Payment.Provider.BKASH,
            transaction_id="bkash_mock_abc123",
        )
        with override_settings(**BKASH_CONFIGURED):
            response = self.client.post(
                "/api/payments/webhooks/bkash/",
                data={"paymentID": mock_payment.transaction_id},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mock", response.data["detail"].lower())

    @override_settings(
        BKASH_APP_KEY="",
        BKASH_APP_SECRET="",
        BKASH_USERNAME="",
        BKASH_PASSWORD="",
    )
    def test_unconfigured_rejected(self):
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"paymentID": "TR0011BKASH"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(**{**BKASH_CONFIGURED, "BKASH_WEBHOOK_SECRET": "shared-secret"})
    def test_hmac_required_when_secret_set(self):
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"paymentID": "TR0011BKASH"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("signature", response.data["detail"].lower())

    @override_settings(**{**BKASH_CONFIGURED, "BKASH_WEBHOOK_SECRET": "shared-secret"})
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._grant_token", return_value="token")
    @patch("apps.payments.strategies.bkash_strategy.BkashStrategy._query")
    def test_valid_hmac_accepted(self, mock_query, _mock_token):
        mock_query.return_value = {
            "paymentID": "TR0011BKASH",
            "transactionStatus": "Completed",
        }
        body = json.dumps({"paymentID": "TR0011BKASH"}).encode("utf-8")
        signature = hmac.new(
            b"shared-secret",
            body,
            hashlib.sha256,
        ).hexdigest()
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data=body,
            content_type="application/json",
            HTTP_X_BKASH_SIGNATURE=f"sha256={signature}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    @override_settings(**BKASH_CONFIGURED)
    @patch(
        "apps.payments.strategies.bkash_strategy.BkashStrategy.handle_webhook",
        return_value=PaymentInitResult(
            transaction_id="missing_tx",
            status="success",
            raw_response={},
        ),
    )
    def test_unknown_payment_ignored(self, _mock_handle):
        response = self.client.post(
            "/api/payments/webhooks/bkash/",
            data={"paymentID": "missing_tx"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "ignored")
