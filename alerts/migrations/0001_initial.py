from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Alert",
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
                ("source", models.CharField(max_length=50)),
                ("source_alert_id", models.CharField(max_length=255)),
                ("object_id", models.CharField(blank=True, max_length=255, null=True)),
                ("observed_at", models.DateTimeField()),
                ("received_at", models.DateTimeField()),
                (
                    "ra_deg",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0")),
                            django.core.validators.MaxValueValidator(Decimal("360")),
                        ],
                    ),
                ),
                (
                    "dec_deg",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=7,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("-90")),
                            django.core.validators.MaxValueValidator(Decimal("90")),
                        ],
                    ),
                ),
                (
                    "magnitude",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=6,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("-100")),
                            django.core.validators.MaxValueValidator(Decimal("100")),
                        ],
                    ),
                ),
                (
                    "magnitude_error",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=6,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(Decimal("0"))],
                    ),
                ),
                ("band", models.CharField(blank=True, max_length=16, null=True)),
                (
                    "alert_class",
                    models.CharField(blank=True, max_length=32, null=True),
                ),
                (
                    "class_confidence",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=4,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0")),
                            django.core.validators.MaxValueValidator(Decimal("1")),
                        ],
                    ),
                ),
                ("cutout_url", models.URLField(blank=True, null=True)),
                ("raw", models.JSONField(default=dict)),
            ],
            options={"ordering": ["-observed_at"]},
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(
                fields=["observed_at"], name="alert_observed_at_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(
                fields=["source", "source_alert_id"], name="alert_source_id_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="alert",
            constraint=models.UniqueConstraint(
                fields=("source", "source_alert_id"),
                name="unique_alert_source_id",
            ),
        ),
    ]
