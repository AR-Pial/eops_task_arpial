import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELED = "canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.PositiveBigIntegerField(unique=True, null=True, blank=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.CASCADE,
        db_index=True,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        ref = f"#{self.number}" if self.number else str(self.id)
        return f"Order {ref} ({self.status})"

    def save(self, *args, **kwargs):
        if self.number is None:
            with transaction.atomic():
                last = (
                    Order.objects.select_for_update()
                    .order_by("-number")
                    .values_list("number", flat=True)
                    .first()
                )
                self.number = (last or 0) + 1
                super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)

    def calculate_total(self) -> Decimal:
        total = sum(
            (item.subtotal for item in self.items.all()),
            Decimal("0.00"),
        )
        self.total_amount = total
        self.save(update_fields=["total_amount", "updated_at"])
        return self.total_amount

    def mark_paid(self) -> None:
        if self.status == self.Status.PAID:
            return
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.status == Order.Status.PAID:
                return
            for item in order.items.select_related("product"):
                item.product.reduce_stock(item.quantity)
            order.status = Order.Status.PAID
            order.save(update_fields=["status", "updated_at"])
            self.status = order.status

    def mark_canceled(self) -> None:
        if self.status != self.Status.PENDING:
            raise ValueError("Only pending orders can be canceled.")
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.status != Order.Status.PENDING:
                raise ValueError("Only pending orders can be canceled.")
            order.status = Order.Status.CANCELED
            order.save(update_fields=["status", "updated_at"])
            self.status = order.status
            from apps.payments.models import Payment

            order.payments.filter(status=Payment.Status.PENDING).update(
                status=Payment.Status.FAILED
            )

    def reopen_for_payment(self) -> None:
        from apps.products.models import Product

        if self.status != self.Status.CANCELED:
            raise ValueError("Only canceled orders can be reopened for payment.")
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.status != Order.Status.CANCELED:
                raise ValueError("Only canceled orders can be reopened for payment.")
            for item in order.items.select_related("product"):
                product = item.product
                if product.status != Product.Status.ACTIVE:
                    raise ValueError(f"Product {product.name} is not available.")
                if product.stock < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock}."
                    )
            order.status = Order.Status.PENDING
            order.save(update_fields=["status", "updated_at"])
            self.status = order.status


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        db_index=True,
    )
    product = models.ForeignKey(
        "products.Product",
        related_name="order_items",
        on_delete=models.PROTECT,
        db_index=True,
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.product_id} x {self.quantity}"

    def calculate_subtotal(self) -> Decimal:
        self.subtotal = (self.price * Decimal(self.quantity)).quantize(Decimal("0.01"))
        return self.subtotal

    def save(self, *args, **kwargs):
        self.calculate_subtotal()
        super().save(*args, **kwargs)
