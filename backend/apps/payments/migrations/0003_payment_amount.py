from decimal import Decimal

from django.db import migrations, models


def backfill_payment_amounts(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    for payment in Payment.objects.select_related("order").iterator():
        payment.amount = payment.order.total_amount
        payment.save(update_fields=["amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_cleanup_duplicate_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="amount",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
            ),
        ),
        migrations.RunPython(backfill_payment_amounts, migrations.RunPython.noop),
    ]
