from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BkashWebhookView,
    CheckoutView,
    ConfirmPaymentView,
    PaymentViewSet,
    StripeWebhookView,
)

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")

urlpatterns = [
    path("checkout/", CheckoutView.as_view()),
    path("confirm/", ConfirmPaymentView.as_view()),
    path("webhooks/stripe/", StripeWebhookView.as_view()),
    path("webhooks/bkash/", BkashWebhookView.as_view()),
    path("", include(router.urls)),
]
