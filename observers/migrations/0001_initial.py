from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import observers.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ObserverProfile",
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
                ("display_name", models.CharField(max_length=100)),
                (
                    "latitude",
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
                    "longitude",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("-180")),
                            django.core.validators.MaxValueValidator(Decimal("180")),
                        ],
                    ),
                ),
                (
                    "elevation_m",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        max_digits=8,
                    ),
                ),
                ("timezone", models.CharField(default="UTC", max_length=63)),
                (
                    "min_altitude_deg",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("30"),
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0")),
                            django.core.validators.MaxValueValidator(Decimal("80")),
                        ],
                    ),
                ),
                (
                    "limiting_magnitude",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("14"),
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("5")),
                            django.core.validators.MaxValueValidator(Decimal("20")),
                        ],
                    ),
                ),
                (
                    "interests",
                    models.JSONField(
                        default=list,
                        validators=[observers.models.validate_interests],
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("system", "System"),
                            ("light", "Light"),
                            ("dark", "Dark"),
                            ("night-red", "Night red"),
                        ],
                        default="system",
                        max_length=9,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observer_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["display_name"]},
        ),
    ]
