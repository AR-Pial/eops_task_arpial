from .bkash_strategy import BkashStrategy
from .stripe_strategy import StripeStrategy


class PaymentStrategyFactory:
    """Resolve a provider name to a PaymentStrategy instance.

    To add a provider: implement PaymentStrategy and register it in _strategies.
    Core order / payment orchestration does not need to change.
    """

    _strategies = {
        "stripe": StripeStrategy,
        "bkash": BkashStrategy,
    }

    @classmethod
    def register(cls, provider: str, strategy_cls) -> None:
        cls._strategies[provider] = strategy_cls

    @classmethod
    def get(cls, provider: str):
        try:
            return cls._strategies[provider]()
        except KeyError as exc:
            raise ValueError(f"Unsupported payment provider: {provider}") from exc
