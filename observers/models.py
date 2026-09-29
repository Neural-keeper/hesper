from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


ALERT_INTERESTS = frozenset(
    {"supernova", "variable_star", "nova", "asteroid", "other"}
)


def validate_interests(value: Any) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValidationError("Interests must be a list of alert class names.")

    unknown_interests = set(value) - ALERT_INTERESTS
    if unknown_interests:
        raise ValidationError(
            "Unknown interests: " + ", ".join(sorted(unknown_interests))
        )


class ObserverProfile(models.Model):
    class Theme(models.TextChoices):
        SYSTEM = "system", "System"
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"
        NIGHT_RED = "night-red", "Night red"

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="observer_profile"
    )
    display_name = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("-90")),
            MaxValueValidator(Decimal("90")),
        ],
    )
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("-180")),
            MaxValueValidator(Decimal("180")),
        ],
    )
    elevation_m = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0")
    )
    timezone = models.CharField(max_length=63, default="UTC")
    min_altitude_deg = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("30"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("80"))],
    )
    limiting_magnitude = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("14"),
        validators=[MinValueValidator(Decimal("5")), MaxValueValidator(Decimal("20"))],
    )
    interests = models.JSONField(default=list, validators=[validate_interests])
    theme = models.CharField(
        max_length=9, choices=Theme.choices, default=Theme.SYSTEM
    )

    class Meta:
        ordering = ["display_name"]

    def __str__(self) -> str:
        return self.display_name
