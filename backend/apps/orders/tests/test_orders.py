from decimal import Decimal

from django.test import TestCase
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.products.models import Product
from apps.test_helpers import (
    auth_client,
    make_order_with_item,
    make_payment,
    make_product,
    make_user,
)


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.product = make_product(price="25.00", stock=10, sku="ORD-M-1")

    def test_save_assigns_sequential_numbers(self):
        first = Order.objects.create(user=self.user)
        second = Order.objects.create(user=self.user)
        self.assertEqual(first.number, 1)
        self.assertEqual(second.number, 2)

    def test_order_item_calculates_subtotal_on_save(self):
        order = Order.objects.create(user=self.user)
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
            price=Decimal("25.00"),
            subtotal=Decimal("0.00"),
        )
        self.assertEqual(item.subtotal, Decimal("75.00"))

    def test_calculate_total(self):
        order = make_order_with_item(self.user, self.product, quantity=2)
        self.assertEqual(order.total_amount, Decimal("50.00"))

    def test_mark_paid_reduces_stock_and_is_idempotent(self):
        order = make_order_with_item(self.user, self.product, quantity=2)
        order.mark_paid()
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 8)

        order.mark_paid()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_mark_canceled_only_from_pending_and_fails_payments(self):
        order = make_order_with_item(self.user, self.product)
        payment = make_payment(order, transaction_id="tx_cancel_1")

        order.mark_canceled()
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELED)
        self.assertEqual(payment.status, Payment.Status.FAILED)

        with self.assertRaises(ValueError):
            order.mark_canceled()

    def test_cannot_cancel_paid_order(self):
        order = make_order_with_item(self.user, self.product)
        order.mark_paid()
        with self.assertRaises(ValueError):
            order.mark_canceled()

    def test_reopen_for_payment(self):
        order = make_order_with_item(self.user, self.product)
        order.mark_canceled()
        order.reopen_for_payment()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_reopen_rejects_insufficient_stock(self):
        order = make_order_with_item(self.user, self.product, quantity=5)
        order.mark_canceled()
        self.product.stock = 1
        self.product.save(update_fields=["stock"])
        with self.assertRaises(ValueError):
            order.reopen_for_payment()

    def test_reopen_rejects_inactive_product(self):
        order = make_order_with_item(self.user, self.product)
        order.mark_canceled()
        self.product.status = Product.Status.INACTIVE
        self.product.save(update_fields=["status"])
        with self.assertRaises(ValueError):
            order.reopen_for_payment()


class OrderAPITests(TestCase):
    def setUp(self):
        self.user = make_user(email="buyer@example.com")
        self.other = make_user(email="other@example.com")
        self.admin = make_user(
            email="admin@example.com",
            user_type="admin",
        )
        self.product = make_product(price="12.50", stock=5, sku="ORD-A-1")
        self.client = auth_client(self.user)

    def test_create_order(self):
        response = self.client.post(
            "/api/orders/",
            {"items": [{"product_id": str(self.product.id), "quantity": 2}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("25.00"))
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)

    def test_create_order_rejects_empty_cart(self):
        response = self.client.post("/api/orders/", {"items": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_rejects_insufficient_stock(self):
        response = self.client.post(
            "/api/orders/",
            {"items": [{"product_id": str(self.product.id), "quantity": 99}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_own_orders(self):
        make_order_with_item(self.user, self.product, quantity=1)
        other_product = make_product(sku="ORD-A-2", stock=3)
        make_order_with_item(self.other, other_product, quantity=1)

        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_lists_all_orders(self):
        make_order_with_item(self.user, self.product)
        admin_client = auth_client(self.admin)
        response = admin_client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_cancel_and_reopen(self):
        order = make_order_with_item(self.user, self.product)
        cancel = self.client.post(f"/api/orders/{order.id}/cancel/")
        self.assertEqual(cancel.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel.data["status"], "canceled")

        reopen = self.client.post(f"/api/orders/{order.id}/reopen/")
        self.assertEqual(reopen.status_code, status.HTTP_200_OK)
        self.assertEqual(reopen.data["status"], "pending")

    def test_cancel_paid_order_returns_400(self):
        order = make_order_with_item(self.user, self.product)
        order.mark_paid()
        response = self.client.post(f"/api/orders/{order.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_access_other_users_order(self):
        order = make_order_with_item(self.other, self.product)
        response = self.client.get(f"/api/orders/{order.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
