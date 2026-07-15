from __future__ import annotations

import logging
import uuid

from django.db import transaction

from apps.orders.models import Order

from .models import Payment
from .strategies import PaymentStrategyFactory

logger = logging.getLogger(__name__)


class PaymentService:
    """Orchestrates checkout/confirm/webhooks via payment strategies."""

    @staticmethod
    @transaction.atomic
    def checkout(order: Order, provider: str) -> tuple[Payment, dict]:
        if order.status == Order.Status.CANCELED:
            order.reopen_for_payment()
        if order.status != Order.Status.PENDING:
            raise ValueError("Only pending orders can be checked out.")

        strategy = PaymentStrategyFactory.get(provider)
        temp_tx = f"pending_{uuid.uuid4().hex}"
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            transaction_id=temp_tx,
            status=Payment.Status.PENDING,
            raw_response={},
        )

        try:
            result = strategy.initiate_payment(order, payment)
        except Exception:
            logger.exception(
                "Payment initiate failed provider=%s order=%s",
                provider,
                order.id,
            )
            payment.delete()
            raise

        payment.transaction_id = result.transaction_id
        payment.status = (
            Payment.Status.SUCCESS
            if result.status == "success"
            else Payment.Status.FAILED
            if result.status == "failed"
            else Payment.Status.PENDING
        )
        payment.raw_response = result.raw_response
        payment.save(
            update_fields=["transaction_id", "status", "raw_response", "updated_at"]
        )

        if payment.status == Payment.Status.SUCCESS:
            order.mark_paid()

        meta = {
            "client_secret": result.client_secret,
            "redirect_url": result.redirect_url,
            "mock": result.mock,
        }
        logger.info(
            "Checkout created payment=%s provider=%s status=%s mock=%s",
            payment.id,
            provider,
            payment.status,
            result.mock,
        )
        return payment, meta

    @staticmethod
    def _apply_result(payment: Payment, result) -> Payment:
        payment.raw_response = result.raw_response
        if result.status == "success":
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            payment.order.mark_paid()
            logger.info(
                "Payment succeeded id=%s order=%s provider=%s",
                payment.id,
                payment.order_id,
                payment.provider,
            )
        elif result.status == "failed":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            order = payment.order
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.CANCELED
                order.save(update_fields=["status", "updated_at"])
            logger.info(
                "Payment failed id=%s order=%s provider=%s",
                payment.id,
                payment.order_id,
                payment.provider,
            )
        else:
            payment.save(update_fields=["raw_response", "updated_at"])
        return payment

    @staticmethod
    @transaction.atomic
    def confirm(payment: Payment, callback_status: str | None = None) -> Payment:
        if payment.status == Payment.Status.SUCCESS:
            return payment

        normalized = (callback_status or "").lower()
        if normalized in ("failure", "failed", "cancel", "cancelled", "canceled"):
            from .strategies.base import PaymentInitResult

            return PaymentService._apply_result(
                payment,
                PaymentInitResult(
                    transaction_id=payment.transaction_id,
                    status="failed",
                    raw_response={
                        **(payment.raw_response or {}),
                        "callback_status": callback_status,
                    },
                ),
            )

        strategy = PaymentStrategyFactory.get(payment.provider)
        try:
            result = strategy.confirm_payment(payment)
        except Exception:
            logger.exception(
                "Payment confirm failed id=%s provider=%s",
                payment.id,
                payment.provider,
            )
            raise
        return PaymentService._apply_result(payment, result)

    @staticmethod
    @transaction.atomic
    def apply_webhook(
        provider: str,
        payload: dict,
        headers: dict,
        *,
        raw_body: bytes | None = None,
    ) -> Payment | None:
        strategy = PaymentStrategyFactory.get(provider)
        result = strategy.handle_webhook(payload, headers, raw_body=raw_body)
        if not result.transaction_id:
            logger.info("Webhook ignored provider=%s (no transaction id)", provider)
            return None
        try:
            payment = Payment.objects.select_for_update().get(
                transaction_id=result.transaction_id
            )
        except Payment.DoesNotExist:
            logger.warning(
                "Webhook payment not found provider=%s tx=%s",
                provider,
                result.transaction_id,
            )
            return None

        if payment.status == Payment.Status.SUCCESS:
            return payment
        return PaymentService._apply_result(payment, result)
