from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings

from .base import PaymentInitResult, PaymentStrategy


class StripeStrategy(PaymentStrategy):
    provider_name = "stripe"

    def _secret_key(self) -> str:
        return getattr(settings, "STRIPE_SECRET_KEY", "") or ""

    def initiate_payment(self, order, payment) -> PaymentInitResult:
        secret = self._secret_key()
        amount_cents = int(order.total_amount * 100)

        if not secret:
            tx = f"pi_mock_{uuid.uuid4().hex[:24]}"
            raw = {
                "id": tx,
                "object": "payment_intent",
                "amount": amount_cents,
                "status": "requires_confirmation",
                "mock": True,
            }
            return PaymentInitResult(
                transaction_id=tx,
                status="pending",
                raw_response=raw,
                client_secret=f"{tx}_secret_mock",
                mock=True,
            )

        import stripe

        stripe.api_key = secret
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={"order_id": str(order.id), "payment_id": str(payment.id)},
            automatic_payment_methods={"enabled": True},
        )
        return PaymentInitResult(
            transaction_id=intent["id"],
            status="pending",
            raw_response=dict(intent),
            client_secret=intent.get("client_secret"),
            mock=False,
        )

    def confirm_payment(self, payment) -> PaymentInitResult:
        secret = self._secret_key()
        tx = payment.transaction_id

        if not secret or str(tx).startswith("pi_mock_"):
            raw = {
                "id": tx,
                "status": "succeeded",
                "mock": True,
            }
            return PaymentInitResult(
                transaction_id=tx,
                status="success",
                raw_response=raw,
                mock=True,
            )

        import stripe

        stripe.api_key = secret
        intent = stripe.PaymentIntent.retrieve(tx)
        status_map = {
            "succeeded": "success",
            "canceled": "failed",
            "requires_payment_method": "failed",
        }
        mapped = status_map.get(intent["status"], "pending")
        return PaymentInitResult(
            transaction_id=intent["id"],
            status=mapped,
            raw_response=dict(intent),
            mock=False,
        )

    def handle_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> PaymentInitResult:
        event_type = payload.get("type", "")
        obj = payload.get("data", {}).get("object", {})
        tx = obj.get("id", "")
        if event_type == "payment_intent.succeeded":
            status = "success"
        elif event_type in (
            "payment_intent.payment_failed",
            "payment_intent.canceled",
        ):
            status = "failed"
        else:
            status = "pending"
        return PaymentInitResult(
            transaction_id=tx,
            status=status,
            raw_response=payload,
            mock=False,
        )
