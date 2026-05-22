from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_order_applied_coupon_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="RazorpayWebhookEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_id", models.CharField(max_length=255, unique=True)),
                ("event_type", models.CharField(max_length=100)),
                ("payload", models.JSONField(default=dict)),
                (
                    "processing_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PROCESSED", "Processed"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Razorpay Webhook Event",
                "verbose_name_plural": "Razorpay Webhook Events",
                "ordering": ["-created_at"],
            },
        ),
    ]
