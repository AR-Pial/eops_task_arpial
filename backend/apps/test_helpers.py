"""Shared helpers for Django TestCase suites."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.products.models import Category, Product

User = get_user_model()


def make_user(
    email: str | None = None,
    password: str = "password123",
    *,
    user_type: str = User.UserType.CUSTOMER,
    **extra,
):
    email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
    return User.objects.create_user(
        email=email,
        password=password,
        user_type=user_type,
        **extra,
    )


def auth_client(user) -> APIClient:
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def make_category(name: str = "Electronics", parent=None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def make_product(
    *,
    name: str = "Widget",
    sku: str | None = None,
    price: str | Decimal = "10.00",
    stock: int = 10,
    status: str = Product.Status.ACTIVE,
    category=None,
) -> Product:
    return Product.objects.create(
        name=name,
        sku=sku or f"SKU-{uuid.uuid4().hex[:12].upper()}",
        price=Decimal(price),
        stock=stock,
        status=status,
        category=category,
    )


def make_order_with_item(
    user,
    product: Product | None = None,
    *,
    quantity: int = 1,
    status: str = Order.Status.PENDING,
) -> Order:
    product = product or make_product()
    order = Order.objects.create(user=user, status=status)
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price,
        subtotal=Decimal("0.00"),
    )
    order.calculate_total()
    return order


def make_payment(
    order: Order,
    *,
    provider: str = Payment.Provider.STRIPE,
    transaction_id: str | None = None,
    status: str = Payment.Status.PENDING,
) -> Payment:
    return Payment.objects.create(
        order=order,
        provider=provider,
        transaction_id=transaction_id or f"tx_{uuid.uuid4().hex[:20]}",
        status=status,
        raw_response={},
    )
