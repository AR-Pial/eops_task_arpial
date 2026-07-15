from __future__ import annotations

import uuid
from typing import Any

import requests
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

    def _base_url(self) -> str:
        return getattr(
            settings,
            "BKASH_BASE_URL",
            "https://tokenized.sandbox.bka.sh/v1.2.0-beta",
        )

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": token,
            "X-APP-Key": settings.BKASH_APP_KEY,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _map_transaction_status(data: dict[str, Any]) -> str:
        status_raw = str(
            data.get("transactionStatus")
            or data.get("status")
            or data.get("trxStatus")
            or ""
        ).lower()
        code = str(data.get("statusCode", ""))

        if status_raw in ("completed", "success"):
            return "success"
        if status_raw in ("failed", "failure", "cancelled", "canceled", "cancel"):
            return "failed"
        if status_raw in ("initiated", "pending"):
            return "pending"
        if code == "0000":
            return "success"
        if code and code != "0000":
            return "failed"
        return "pending"

    def initiate_payment(self, order, payment) -> PaymentInitResult:
        if not self._configured():
            tx = f"bkash_mock_{uuid.uuid4().hex[:20]}"
            raw = {
                "paymentID": tx,
                "amount": str(order.total_amount),
                "statusCode": "0000",
                "mock": True,
            }
            return PaymentInitResult(
                transaction_id=tx,
                status="pending",
                raw_response=raw,
                mock=True,
            )

        callback = getattr(settings, "BKASH_CALLBACK_URL", "") or ""
        if not callback:
            raise ValueError("bKash is not configured correctly.")

        base = self._base_url()
        token = self._grant_token(base)
        payload = {
            "mode": "0011",
            "payerReference": str(order.user_id)[:20],
            "callbackURL": callback,
            "amount": str(order.total_amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": str(payment.id).replace("-", "")[:30],
        }
        resp = requests.post(
            f"{base}/tokenized/checkout/create",
            json=payload,
            headers=self._headers(token),
            timeout=30,
        )
        try:
            data = resp.json()
        except ValueError as exc:
            raise ValueError(f"bKash create returned invalid JSON ({resp.status_code})") from exc

        if resp.status_code >= 400 or str(data.get("statusCode", "0000")) != "0000":
            message = (
                data.get("statusMessage")
                or data.get("errorMessage")
                or data.get("message")
                or f"bKash create failed ({resp.status_code})"
            )
            raise ValueError(str(message))

        tx = data.get("paymentID") or data.get("paymentId")
        redirect = data.get("bkashURL") or data.get("bkashUrl")
        if not tx or not redirect:
            raise ValueError("bKash create did not return paymentID/bkashURL.")

        return PaymentInitResult(
            transaction_id=tx,
            status="pending",
            raw_response=data,
            redirect_url=redirect,
            mock=False,
        )

    def _grant_token(self, base: str) -> str:
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
        try:
            data = resp.json()
        except ValueError as exc:
            raise ValueError(f"bKash grant token returned invalid JSON ({resp.status_code})") from exc

        token = data.get("id_token") or data.get("token") or ""
        if not token:
            message = (
                data.get("statusMessage")
                or data.get("errorMessage")
                or data.get("msg")
                or "bKash grant token failed"
            )
            raise ValueError(str(message))
        return token

    def _execute(self, base: str, token: str, payment_id: str) -> dict[str, Any]:
        resp = requests.post(
            f"{base}/tokenized/checkout/execute",
            json={"paymentID": payment_id},
            headers=self._headers(token),
            timeout=30,
        )
        try:
            return resp.json()
        except ValueError as exc:
            raise ValueError(f"bKash execute returned invalid JSON ({resp.status_code})") from exc

    def _query(self, base: str, token: str, payment_id: str) -> dict[str, Any]:
        resp = requests.post(
            f"{base}/tokenized/checkout/payment/status",
            json={"paymentID": payment_id},
            headers=self._headers(token),
            timeout=30,
        )
        try:
            return resp.json()
        except ValueError as exc:
            raise ValueError(f"bKash query returned invalid JSON ({resp.status_code})") from exc

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

        base = self._base_url()
        token = self._grant_token(base)

        try:
            data = self._execute(base, token, tx)
        except (requests.RequestException, ValueError):
            data = self._query(base, token, tx)

        mapped = self._map_transaction_status(data)
        if mapped == "pending":
            try:
                queried = self._query(base, token, tx)
                mapped = self._map_transaction_status(queried)
                data = {"execute": data, "query": queried}
            except (requests.RequestException, ValueError):
                pass

        return PaymentInitResult(
            transaction_id=tx,
            status=mapped,
            raw_response=data,
            mock=False,
        )

    def handle_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> PaymentInitResult:
        tx = str(payload.get("paymentID") or payload.get("transaction_id") or "")
        status = self._map_transaction_status(payload)
        return PaymentInitResult(
            transaction_id=tx,
            status=status,
            raw_response=payload,
            mock=False,
        )
