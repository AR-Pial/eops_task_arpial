from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.products.models import Category, Product
from apps.test_helpers import make_category, make_product


class CategoryModelTests(TestCase):
    def test_parent_child_relationship(self):
        root = make_category("Root")
        child = make_category("Child", parent=root)
        self.assertEqual(child.parent_id, root.id)
        self.assertIn(child, root.children.all())

    def test_str(self):
        cat = make_category("Gadgets")
        self.assertEqual(str(cat), "Gadgets")


class ProductModelTests(TestCase):
    def test_reduce_stock_success(self):
        product = make_product(stock=5)
        product.reduce_stock(2)
        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

    def test_reduce_stock_rejects_non_positive(self):
        product = make_product(stock=5)
        with self.assertRaises(ValueError):
            product.reduce_stock(0)
        with self.assertRaises(ValueError):
            product.reduce_stock(-1)

    def test_reduce_stock_insufficient(self):
        product = make_product(stock=1)
        with self.assertRaises(ValueError):
            product.reduce_stock(2)
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)

    def test_sku_must_be_unique(self):
        make_product(sku="UNIQUE-1")
        with self.assertRaises(IntegrityError):
            make_product(name="Other", sku="UNIQUE-1")

    def test_category_set_null_on_delete(self):
        category = make_category()
        product = make_product(category=category, sku="CAT-1")
        category.delete()
        product.refresh_from_db()
        self.assertIsNone(product.category_id)

    def test_defaults(self):
        product = Product.objects.create(
            name="Bare",
            sku="BARE-1",
            price=Decimal("1.50"),
        )
        self.assertEqual(product.stock, 0)
        self.assertEqual(product.status, Product.Status.ACTIVE)
        self.assertFalse(product.is_featured)
