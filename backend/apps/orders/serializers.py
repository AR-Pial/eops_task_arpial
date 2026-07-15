from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.payments.models import Payment
from apps.products.models import Product

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("name", "quantity", "price", "subtotal")


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderPaymentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("provider", "transaction_id", "amount", "status", "created_at")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = OrderPaymentBriefSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "user",
            "user_email",
            "user_first_name",
            "user_last_name",
            "total_amount",
            "status",
            "items",
            "payments",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Cart cannot be empty.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        order = Order.objects.create(user=user, status=Order.Status.PENDING)

        for row in validated_data["items"]:
            try:
                product = Product.objects.select_for_update().get(pk=row["product_id"])
            except Product.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"items": f"Product {row['product_id']} not found."}
                ) from exc

            if product.status != Product.Status.ACTIVE:
                raise serializers.ValidationError(
                    {"items": f"Product {product.name} is not available."}
                )
            if product.stock < row["quantity"]:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Insufficient stock for {product.name}. "
                            f"Available: {product.stock}."
                        )
                    }
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=row["quantity"],
                price=product.price,
                subtotal=(product.price * Decimal(row["quantity"])).quantize(
                    Decimal("0.01")
                ),
            )

        order.calculate_total()
        return order
