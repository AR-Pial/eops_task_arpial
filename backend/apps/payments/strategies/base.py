from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PaymentInitResult:
    transaction_id: str
    status: str
    raw_response: dict[str, Any]
    client_secret: str | None = None
    redirect_url: str | None = None
    mock: bool = False


class PaymentStrategy(ABC):
    """Strategy interface for payment providers."""

    provider_name: str

    @abstractmethod
    def initiate_payment(self, order, payment) -> PaymentInitResult:
        """Create provider-side payment (intent / checkout)."""

    @abstractmethod
    def confirm_payment(self, payment) -> PaymentInitResult:
        """Confirm / execute / query payment status."""

    def handle_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> PaymentInitResult:
        raise NotImplementedError
