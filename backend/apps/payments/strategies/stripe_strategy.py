from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

from .base import PaymentInitResult, PaymentStrategy

logger = logging.getLogger(__name__)


class StripeStrategy(PaymentStrategy):
    provider_name = "stripe"

    def _secret_key(self) -> str:
        return getattr(settings, "STRIPE_SECRET_KEY", "") or ""

    def _webhook_secret(self) -> str:
        return getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""

    def initiate_payment(self, order, payment) -> PaymentInitResult:
        secret = self._secret_key()
        amount_cents = int(order.total_amount * 100)

        if not secret:
            import uuid

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
            raw_response=intent.to_dict(),
            client_secret=intent["client_secret"],
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
            raw_response=intent.to_dict(),
            mock=False,
        )

    def handle_webhook(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
        *,
        raw_body: bytes | None = None,
    ) -> PaymentInitResult:
        webhook_secret = self._webhook_secret()
        event_payload: dict[str, Any] = payload or {}

        if webhook_secret:
            if raw_body is None:
                raise ValueError("Stripe webhook requires the raw request body.")
            signature = (
                headers.get("Stripe-Signature")
                or headers.get("stripe-signature")
                or ""
            )
            if not signature:
                raise ValueError("Missing Stripe-Signature header.")

            import stripe

            try:
                event = stripe.Webhook.construct_event(
                    payload=raw_body,
                    sig_header=signature,
                    secret=webhook_secret,
                )
            except stripe.SignatureVerificationError as exc:
                logger.warning("Stripe webhook signature verification failed: %s", exc)
                raise ValueError("Invalid Stripe webhook signature.") from exc
            except Exception as exc:  # noqa: BLE001
                logger.warning("Stripe webhook construct_event failed: %s", exc)
                raise ValueError("Invalid Stripe webhook payload.") from exc

            event_payload = event.to_dict() if hasattr(event, "to_dict") else dict(event)
        elif raw_body and not event_payload:
            try:
                event_payload = json.loads(raw_body)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid Stripe webhook JSON.") from exc
            logger.warning(
                "STRIPE_WEBHOOK_SECRET unset; accepting unverified Stripe webhook."
            )

        event_type = event_payload.get("type", "")
        obj = event_payload.get("data", {}).get("object", {})
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
            raw_response=event_payload,
            mock=False,
        )
