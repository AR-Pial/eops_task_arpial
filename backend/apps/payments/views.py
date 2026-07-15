import logging

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import (
    CheckoutSerializer,
    ConfirmPaymentSerializer,
    PaymentSerializer,
)
from .services import PaymentService

logger = logging.getLogger(__name__)


class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = Payment.objects.select_related("order").order_by("-created_at")
        user = self.request.user
        if getattr(user, "user_type", None) in ("admin", "superadmin"):
            return qs
        return qs.filter(order__user=user)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.context["order"]
        provider = serializer.validated_data["provider"]
        try:
            payment, meta = PaymentService.checkout(order, provider)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Checkout provider error order=%s provider=%s", order.id, provider)
            return Response(
                {"detail": str(exc) or "Payment provider error."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = PaymentSerializer(payment).data
        data.update(meta)
        return Response(data, status=status.HTTP_201_CREATED)


class ConfirmPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConfirmPaymentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            payment = PaymentService.confirm(
                serializer.context["payment"],
                callback_status=serializer.validated_data.get("callback_status"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Confirm payment error")
            return Response(
                {"detail": str(exc) or "Payment confirmation failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(PaymentSerializer(payment).data)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body
        headers = {k: v for k, v in request.headers.items()}
        try:
            payment = PaymentService.apply_webhook(
                "stripe",
                request.data if isinstance(request.data, dict) else {},
                headers,
                raw_body=raw_body,
            )
        except ValueError as exc:
            logger.warning("Stripe webhook rejected: %s", exc)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Stripe webhook failed")
            return Response(
                {"detail": "Webhook processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if not payment:
            return Response({"detail": "ignored"}, status=status.HTTP_200_OK)
        return Response(PaymentSerializer(payment).data)


class BkashWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body
        headers = {k: v for k, v in request.headers.items()}
        try:
            payment = PaymentService.apply_webhook(
                "bkash",
                request.data if isinstance(request.data, dict) else {},
                headers,
                raw_body=raw_body,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("bKash webhook failed")
            return Response(
                {"detail": "Webhook processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if not payment:
            return Response({"detail": "ignored"}, status=status.HTTP_200_OK)
        return Response(PaymentSerializer(payment).data)
