from rest_framework import serializers

from apps.orders.models import Order

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.IntegerField(source="order.number", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "order_number",
            "order_status",
            "amount",
            "provider",
            "transaction_id",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutResponseSerializer(PaymentSerializer):
    """Payment row plus provider client fields returned by checkout."""

    client_secret = serializers.CharField(allow_null=True, required=False)
    redirect_url = serializers.CharField(allow_null=True, required=False)
    mock = serializers.BooleanField(required=False)

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + (
            "client_secret",
            "redirect_url",
            "mock",
        )


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
        if order.status == Order.Status.CANCELED:
            try:
                order.reopen_for_payment()
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        elif order.status != Order.Status.PENDING:
            raise serializers.ValidationError("Order cannot be paid.")
        self.context["order"] = order
        return value


class ConfirmPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField(required=False)
    transaction_id = serializers.CharField(required=False, max_length=255)
    callback_status = serializers.ChoiceField(
        choices=("success", "failure", "cancel"),
        required=False,
    )

    def validate(self, attrs):
        payment_id = attrs.get("payment_id")
        transaction_id = attrs.get("transaction_id")
        if not payment_id and not transaction_id:
            raise serializers.ValidationError(
                "Provide payment_id or transaction_id."
            )

        user = self.context["request"].user
        try:
            if payment_id:
                payment = Payment.objects.select_related("order").get(pk=payment_id)
            else:
                payment = Payment.objects.select_related("order").get(
                    transaction_id=transaction_id
                )
        except Payment.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"payment_id": "Payment not found."}
                if payment_id
                else {"transaction_id": "Payment not found."}
            ) from exc

        if payment.order.user_id != user.id and getattr(user, "user_type", None) not in (
            "admin",
            "superadmin",
        ):
            raise serializers.ValidationError(
                {"payment_id": "Payment not found."}
                if payment_id
                else {"transaction_id": "Payment not found."}
            )

        self.context["payment"] = payment
        return attrs
