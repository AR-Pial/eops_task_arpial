import uuid
from decimal import Decimal

from django.db import models


class Payment(models.Model):
    """Provider-agnostic payment record linked to an order."""

    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        BKASH = "bkash", "bKash"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order",
        related_name="payments",
        on_delete=models.CASCADE,
        db_index=True,
    )
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        db_index=True,
    )
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"

    def __str__(self):
        return f"{self.provider}:{self.transaction_id} ({self.status})"
