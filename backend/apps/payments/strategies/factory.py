from .bkash_strategy import BkashStrategy
from .stripe_strategy import StripeStrategy


class PaymentStrategyFactory:
    _strategies = {
        "stripe": StripeStrategy,
        "bkash": BkashStrategy,
    }

    @classmethod
    def get(cls, provider: str):
        try:
            return cls._strategies[provider]()
        except KeyError as exc:
            raise ValueError(f"Unsupported payment provider: {provider}") from exc
