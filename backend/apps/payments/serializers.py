from rest_framework import serializers

from apps.orders.models import Order

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="order.id", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "order_id",
            "provider",
            "transaction_id",
            "status",
            "raw_response",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=Payment.Provider.choices)

    def validate_order_id(self, value):
        user = self.context["request"].user
        try:
            order = Order.objects.get(pk=value)
        except Order.DoesNotExist as exc:
            raise serializers.ValidationError("Order not found.") from exc
        if order.user_id != user.id and getattr(user, "user_type", None) not in (
            "admin",
            "superadmin",
        ):
            raise serializers.ValidationError("Order not found.")
        if order.status != Order.Status.PENDING:
            raise serializers.ValidationError("Order is not pending.")
        self.context["order"] = order
        return value


class ConfirmPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()

    def validate_payment_id(self, value):
        user = self.context["request"].user
        try:
            payment = Payment.objects.select_related("order").get(pk=value)
        except Payment.DoesNotExist as exc:
            raise serializers.ValidationError("Payment not found.") from exc
        if payment.order.user_id != user.id and getattr(user, "user_type", None) not in (
            "admin",
            "superadmin",
        ):
            raise serializers.ValidationError("Payment not found.")
        self.context["payment"] = payment
        return value
