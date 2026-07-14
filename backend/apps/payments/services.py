from __future__ import annotations

import uuid

from django.db import transaction

from apps.orders.models import Order

from .models import Payment
from .strategies import PaymentStrategyFactory


class PaymentService:
    """Coordinates order + payment flow without coupling to a provider."""

    @staticmethod
    @transaction.atomic
    def checkout(order: Order, provider: str) -> tuple[Payment, dict]:
        if order.status != Order.Status.PENDING:
            raise ValueError("Only pending orders can be checked out.")

        strategy = PaymentStrategyFactory.get(provider)
        # Temporary unique transaction_id until provider assigns one.
        temp_tx = f"pending_{uuid.uuid4().hex}"
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            transaction_id=temp_tx,
            status=Payment.Status.PENDING,
            raw_response={},
        )

        result = strategy.initiate_payment(order, payment)
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
        return payment, meta

    @staticmethod
    @transaction.atomic
    def confirm(payment: Payment) -> Payment:
        if payment.status == Payment.Status.SUCCESS:
            return payment

        strategy = PaymentStrategyFactory.get(payment.provider)
        result = strategy.confirm_payment(payment)
        payment.raw_response = result.raw_response
        if result.status == "success":
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            payment.order.mark_paid()
        elif result.status == "failed":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            order = payment.order
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.CANCELED
                order.save(update_fields=["status", "updated_at"])
        else:
            payment.save(update_fields=["raw_response", "updated_at"])
        return payment

    @staticmethod
    @transaction.atomic
    def apply_webhook(provider: str, payload: dict, headers: dict) -> Payment | None:
        strategy = PaymentStrategyFactory.get(provider)
        result = strategy.handle_webhook(payload, headers)
        if not result.transaction_id:
            return None
        try:
            payment = Payment.objects.select_for_update().get(
                transaction_id=result.transaction_id
            )
        except Payment.DoesNotExist:
            return None

        payment.raw_response = result.raw_response
        if result.status == "success":
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            payment.order.mark_paid()
        elif result.status == "failed":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "raw_response", "updated_at"])
        else:
            payment.save(update_fields=["raw_response", "updated_at"])
        return payment
