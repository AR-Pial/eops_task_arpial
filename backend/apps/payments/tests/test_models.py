from decimal import Decimal

from django.test import TestCase

from apps.payments.models import Payment
from apps.test_helpers import make_order_with_item, make_payment, make_user


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.order = make_order_with_item(self.user)

    def test_defaults_and_str(self):
        payment = make_payment(self.order, transaction_id="tx_model_1")
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.raw_response, {})
        self.assertEqual(payment.amount, self.order.total_amount)
        self.assertIn("tx_model_1", str(payment))

    def test_amount_persisted_independently_of_order(self):
        payment = make_payment(
            self.order,
            transaction_id="tx_amount_snap",
            amount=Decimal("42.50"),
        )
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("42.50"))
        self.assertNotEqual(payment.amount, self.order.total_amount)

    def test_transaction_id_unique(self):
        from django.db import IntegrityError

        make_payment(self.order, transaction_id="tx_unique")
        other = make_order_with_item(self.user)
        with self.assertRaises(IntegrityError):
            make_payment(other, transaction_id="tx_unique")
