from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at")
    search_fields = ("name",)
    list_filter = ("parent",)
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "stock",
        "is_featured",
        "status",
        "created_at",
    )
    list_filter = ("status", "is_featured", "category")
    search_fields = ("name", "sku")
    ordering = ("-is_featured", "-created_at")
    list_editable = ("is_featured",)
    readonly_fields = ("id", "created_at", "updated_at")
