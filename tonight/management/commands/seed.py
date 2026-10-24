from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from alerts.models import Alert
from observers.models import ObserverProfile


class Command(BaseCommand):
    help = "Create an idempotent demo observer and sample alerts."

    def handle(self, *args: object, **options: object) -> None:
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com", "first_name": "Demo"},
        )
        if created:
            user.set_password("demo")
            user.save(update_fields=["password"])
        profile, _ = ObserverProfile.objects.get_or_create(
            user=user,
            defaults={
                "display_name": "Demo observer",
                "latitude": Decimal("27.9500"),
                "longitude": Decimal("-82.4600"),
                "elevation_m": Decimal("10"),
                "timezone": "America/New_York",
                "min_altitude_deg": Decimal("30"),
                "limiting_magnitude": Decimal("14"),
                "interests": ["supernova", "variable_star", "nova", "asteroid"],
            },
        )
        now = datetime.now(timezone.utc)
        samples = (
            (
                "sample-orion",
                Decimal("83.8"),
                Decimal("-5.4"),
                Decimal("12.4"),
                "supernova",
            ),
            (
                "sample-southern",
                Decimal("120"),
                Decimal("-70"),
                Decimal("11.8"),
                "nova",
            ),
        )
        for identifier, ra, dec, magnitude, alert_class in samples:
            Alert.objects.get_or_create(
                source="sample",
                source_alert_id=identifier,
                defaults={
                    "observed_at": now - timedelta(hours=6),
                    "received_at": now,
                    "ra_deg": ra,
                    "dec_deg": dec,
                    "magnitude": magnitude,
                    "band": "r",
                    "alert_class": alert_class,
                    "class_confidence": Decimal("0.82"),
                    "raw": {"sample": True, "identifier": identifier},
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo user ready: username=demo password=demo "
                f"(profile id {profile.pk})"
            )
        )
