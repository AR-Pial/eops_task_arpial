from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings

from .base import PaymentInitResult, PaymentStrategy


class BkashStrategy(PaymentStrategy):
    provider_name = "bkash"

    def _configured(self) -> bool:
        return bool(
            getattr(settings, "BKASH_APP_KEY", "")
            and getattr(settings, "BKASH_APP_SECRET", "")
            and getattr(settings, "BKASH_USERNAME", "")
            and getattr(settings, "BKASH_PASSWORD", "")
        )

    def initiate_payment(self, order, payment) -> PaymentInitResult:
        if not self._configured():
            tx = f"bkash_mock_{uuid.uuid4().hex[:20]}"
            raw = {
                "paymentID": tx,
                "bkashURL": f"https://sandbox.pay.bka.sh/mock/{tx}",
                "amount": str(order.total_amount),
                "statusCode": "0000",
                "mock": True,
            }
            return PaymentInitResult(
                transaction_id=tx,
                status="pending",
                raw_response=raw,
                redirect_url=raw["bkashURL"],
                mock=True,
            )

        # Real bKash Create Payment uses grant token + create API.
        # Credentials present: call sandbox/live create endpoint.
        import requests

        base = getattr(
            settings,
            "BKASH_BASE_URL",
            "https://tokenized.sandbox.bka.sh/v1.2.0-beta",
        )
        token = self._grant_token(base)
        payload = {
            "mode": "0011",
            "payerReference": str(order.user_id)[:20],
            "callbackURL": getattr(settings, "BKASH_CALLBACK_URL", ""),
            "amount": str(order.total_amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": str(order.id).replace("-", "")[:30],
        }
        resp = requests.post(
            f"{base}/tokenized/checkout/create",
            json=payload,
            headers={
                "Authorization": token,
                "X-APP-Key": settings.BKASH_APP_KEY,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        data = resp.json()
        tx = data.get("paymentID") or data.get("paymentId") or f"bkash_{uuid.uuid4().hex[:16]}"
        return PaymentInitResult(
            transaction_id=tx,
            status="pending",
            raw_response=data,
            redirect_url=data.get("bkashURL"),
            mock=False,
        )

    def _grant_token(self, base: str) -> str:
        import requests

        resp = requests.post(
            f"{base}/tokenized/checkout/token/grant",
            json={
                "app_key": settings.BKASH_APP_KEY,
                "app_secret": settings.BKASH_APP_SECRET,
            },
            headers={
                "username": settings.BKASH_USERNAME,
                "password": settings.BKASH_PASSWORD,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        data = resp.json()
        return data.get("id_token") or data.get("token") or ""

    def confirm_payment(self, payment) -> PaymentInitResult:
        tx = payment.transaction_id
        if not self._configured() or str(tx).startswith("bkash_mock_"):
            raw = {"paymentID": tx, "transactionStatus": "Completed", "mock": True}
            return PaymentInitResult(
                transaction_id=tx,
                status="success",
                raw_response=raw,
                mock=True,
            )

        import requests

        base = getattr(
            settings,
            "BKASH_BASE_URL",
            "https://tokenized.sandbox.bka.sh/v1.2.0-beta",
        )
        token = self._grant_token(base)
        resp = requests.post(
            f"{base}/tokenized/checkout/execute",
            json={"paymentID": tx},
            headers={
                "Authorization": token,
                "X-APP-Key": settings.BKASH_APP_KEY,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        data = resp.json()
        ok = str(data.get("transactionStatus", "")).lower() in (
            "completed",
            "success",
        ) or data.get("statusCode") == "0000"
        return PaymentInitResult(
            transaction_id=tx,
            status="success" if ok else "failed",
            raw_response=data,
            mock=False,
        )

    def handle_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> PaymentInitResult:
        tx = payload.get("paymentID") or payload.get("transaction_id") or ""
        status_raw = str(payload.get("transactionStatus", payload.get("status", ""))).lower()
        if status_raw in ("completed", "success"):
            status = "success"
        elif status_raw in ("failed", "cancelled", "canceled"):
            status = "failed"
        else:
            status = "pending"
        return PaymentInitResult(
            transaction_id=tx,
            status=status,
            raw_response=payload,
            mock=False,
        )
