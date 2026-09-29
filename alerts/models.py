from decimal import Decimal
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Alert(models.Model):
    source = models.CharField(max_length=50)
    source_alert_id = models.CharField(max_length=255)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    observed_at = models.DateTimeField()
    received_at = models.DateTimeField()
    ra_deg = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("360"))],
    )
    dec_deg = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("-90")),
            MaxValueValidator(Decimal("90")),
        ],
    )
    magnitude = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal("-100")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    magnitude_error = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    band = models.CharField(max_length=16, blank=True, null=True)
    alert_class = models.CharField(max_length=32, blank=True, null=True)
    class_confidence = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("1")),
        ],
    )
    cutout_url = models.URLField(blank=True, null=True)
    raw = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_alert_id"],
                name="unique_alert_source_id",
            )
        ]
        indexes = [
            models.Index(fields=["observed_at"], name="alert_observed_at_idx"),
            models.Index(
                fields=["source", "source_alert_id"], name="alert_source_id_idx"
            ),
        ]
        ordering = ["-observed_at"]

    def __str__(self) -> str:
        return f"{self.source}:{self.source_alert_id}"
