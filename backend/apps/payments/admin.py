from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider",
        "transaction_id",
        "status",
        "created_at",
    )
    list_filter = ("provider", "status")
    search_fields = ("transaction_id", "order__id")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
