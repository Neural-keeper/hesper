from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from alerts.models import Alert


class Command(BaseCommand):
    help = "Delete alerts older than the configured retention period."

    def handle(self, *args: object, **options: object) -> None:
        cutoff = timezone.now() - timedelta(days=settings.ALERT_RETENTION_DAYS)
        deleted, _ = Alert.objects.filter(observed_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} records older than "
                f"{settings.ALERT_RETENTION_DAYS} days."
            )
        )
