from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.products.category_cache import invalidate_category_tree
from apps.products.models import Category, Product

User = get_user_model()

DEFAULT_ADMIN_EMAIL = "admin@eops.local"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Nested category tree used by seed (name -> children or None).
CATEGORY_TREE = {
    "Electronics": {
        "Phones": None,
        "Laptops": None,
        "Accessories": None,
    },
    "Clothing": {
        "Men": None,
        "Women": None,
    },
    "Home & Living": {
        "Kitchen": None,
        "Decor": None,
    },
}

# sku, name, category path, price, stock, featured, description
SAMPLE_PRODUCTS = [
    (
        "PHONE-001",
        "Pixel Nova X",
        ("Electronics", "Phones"),
        "699.00",
        25,
        True,
        "Flagship Android phone with OLED display.",
    ),
    (
        "PHONE-002",
        "Aurora SE",
        ("Electronics", "Phones"),
        "449.00",
        40,
        False,
        "Compact mid-range phone for daily use.",
    ),
    (
        "LAP-001",
        "Workbench Pro 14",
        ("Electronics", "Laptops"),
        "1299.00",
        15,
        True,
        "14-inch developer laptop with long battery life.",
    ),
    (
        "LAP-002",
        "CloudBook Air",
        ("Electronics", "Laptops"),
        "899.00",
        20,
        False,
        "Lightweight laptop for travel and office work.",
    ),
    (
        "ACC-001",
        "USB-C Hub 7-in-1",
        ("Electronics", "Accessories"),
        "59.00",
        80,
        False,
        "HDMI, USB-A, SD, and Ethernet in one hub.",
    ),
    (
        "ACC-002",
        "Wireless Buds Mini",
        ("Electronics", "Accessories"),
        "79.00",
        60,
        True,
        "Noise-isolating earbuds with charging case.",
    ),
    (
        "MEN-001",
        "Everyday Crew Tee",
        ("Clothing", "Men"),
        "24.00",
        100,
        False,
        "Soft cotton crew-neck t-shirt.",
    ),
    (
        "MEN-002",
        "Stretch Chino Pants",
        ("Clothing", "Men"),
        "54.00",
        45,
        False,
        "Slim-fit chinos with stretch fabric.",
    ),
    (
        "WOM-001",
        "Linen Summer Shirt",
        ("Clothing", "Women"),
        "48.00",
        55,
        True,
        "Breathable linen shirt for warm weather.",
    ),
    (
        "WOM-002",
        "High-Rise Denim",
        ("Clothing", "Women"),
        "68.00",
        35,
        False,
        "Classic high-rise jeans with straight leg.",
    ),
    (
        "KIT-001",
        "Ceramic Pour-Over Set",
        ("Home & Living", "Kitchen"),
        "42.00",
        30,
        False,
        "Dripper, mug, and filters for pour-over coffee.",
    ),
    (
        "KIT-002",
        "Nonstick Skillet 10\"",
        ("Home & Living", "Kitchen"),
        "39.00",
        50,
        False,
        "Everyday skillet with heat-safe handle.",
    ),
    (
        "DEC-001",
        "Oak Desk Lamp",
        ("Home & Living", "Decor"),
        "65.00",
        22,
        True,
        "Warm LED desk lamp with oak base.",
    ),
    (
        "DEC-002",
        "Woven Throw Blanket",
        ("Home & Living", "Decor"),
        "49.00",
        28,
        False,
        "Soft cotton throw for sofa or bed.",
    ),
]


class Command(BaseCommand):
    help = "Seed an admin user and sample categories/products for local demos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=DEFAULT_ADMIN_EMAIL,
            help=f"Admin email (default: {DEFAULT_ADMIN_EMAIL})",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_ADMIN_PASSWORD,
            help=f"Admin password (default: {DEFAULT_ADMIN_PASSWORD})",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing categories and products before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        clear = options["clear"]

        admin = self._seed_admin(email, password)
        if clear:
            deleted_products, _ = Product.objects.all().delete()
            deleted_categories, _ = Category.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Cleared {deleted_products} products and {deleted_categories} categories."
                )
            )

        categories = self._seed_categories()
        created_products, updated_products = self._seed_products(categories)
        invalidate_category_tree()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded admin {admin.email} ({admin.user_type}); "
                f"{len(categories)} categories; "
                f"{created_products} products created, {updated_products} updated."
            )
        )
        self.stdout.write(f"  Login: {email} / {password}")

    def _seed_admin(self, email: str, password: str) -> User:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Demo",
                "last_name": "Admin",
                "user_type": User.UserType.SUPERADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {email}"))
            return user

        changed = False
        if user.user_type != User.UserType.SUPERADMIN:
            user.user_type = User.UserType.SUPERADMIN
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        user.set_password(password)
        update_fields = ["password"]
        if changed:
            update_fields.extend(["user_type", "is_staff", "is_superuser", "is_active"])
        user.save(update_fields=update_fields)
        self.stdout.write(f"Updated admin user: {email}")
        return user

    def _seed_categories(self) -> dict[tuple[str, ...], Category]:
        """Create the category tree; return map of path tuple -> Category."""
        by_path: dict[tuple[str, ...], Category] = {}

        def walk(tree: dict, parent: Category | None, path: tuple[str, ...]) -> None:
            for name, children in tree.items():
                current_path = path + (name,)
                category, created = Category.objects.get_or_create(
                    name=name,
                    parent=parent,
                )
                by_path[current_path] = category
                action = "Created" if created else "Found"
                self.stdout.write(f"  {action} category: {' / '.join(current_path)}")
                if children:
                    walk(children, category, current_path)

        walk(CATEGORY_TREE, None, ())
        return by_path

    def _seed_products(
        self, categories: dict[tuple[str, ...], Category]
    ) -> tuple[int, int]:
        created_count = 0
        updated_count = 0

        for sku, name, path, price, stock, featured, description in SAMPLE_PRODUCTS:
            category = categories[path]
            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "description": description,
                    "price": Decimal(price),
                    "stock": stock,
                    "is_featured": featured,
                    "status": Product.Status.ACTIVE,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created product: {sku} — {product.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  Updated product: {sku} — {product.name}")

        return created_count, updated_count
