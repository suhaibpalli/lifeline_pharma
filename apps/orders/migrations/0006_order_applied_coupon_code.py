from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_add_razorpay_order_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="applied_coupon_code",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
