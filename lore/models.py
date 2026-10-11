from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SkyCulture(models.Model):
    name = models.CharField(max_length=100, unique=True)
    region_or_people = models.CharField(max_length=100)
    description = models.TextField()
    source_url = models.URLField()
    license = models.CharField(max_length=100)
    credit_text = models.TextField()

    def __str__(self) -> str:
        return self.name


class Star(models.Model):
    hip_number = models.PositiveIntegerField(unique=True)
    proper_name = models.CharField(max_length=255, blank=True, null=True)
    ra_deg = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(360)]
    )
    dec_deg = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    magnitude = models.FloatField()

    def __str__(self) -> str:
        return self.proper_name or f"HIP {self.hip_number}"


class CulturalConstellation(models.Model):
    culture = models.ForeignKey(
        SkyCulture,
        on_delete=models.CASCADE,
        related_name="constellations",
    )
    native_name = models.CharField(max_length=255)
    english_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    stars = models.JSONField(default=list)
    source_url = models.URLField()
    license = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["culture", "native_name"],
                name="unique_cultural_constellation_name",
            )
        ]

    def __str__(self) -> str:
        return self.english_name or self.native_name
