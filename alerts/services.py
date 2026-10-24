from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.db import IntegrityError

from .models import Alert, IngestionState
from .sources.alerce import AlerceSource
from .sources.base import AlertSource
from .sources.sample import SampleSource

logger = logging.getLogger(__name__)


def get_source(name: str) -> AlertSource:
    if name == "alerce":
        return AlerceSource()
    if name == "sample":
        return SampleSource()
    raise ValueError(f"Unsupported alert source: {name}")


def ingest(source: AlertSource, since: datetime) -> tuple[int, int, int]:
    created = skipped = invalid = 0
    for normalized in source.fetch(since):
        if normalized.magnitude > settings.INGEST_MAX_MAGNITUDE:
            skipped += 1
            continue
        if Alert.objects.filter(
            source=normalized.source,
            source_alert_id=normalized.source_alert_id,
        ).exists():
            skipped += 1
            continue
        try:
            alert = Alert(
                source=normalized.source,
                source_alert_id=normalized.source_alert_id,
                object_id=normalized.object_id,
                observed_at=normalized.observed_at,
                received_at=normalized.received_at,
                ra_deg=normalized.ra_deg,
                dec_deg=normalized.dec_deg,
                magnitude=normalized.magnitude,
                magnitude_error=normalized.magnitude_error,
                band=normalized.band,
                alert_class=normalized.alert_class,
                class_confidence=normalized.class_confidence,
                cutout_url=normalized.cutout_url,
                raw=normalized.raw,
            )
            alert.full_clean()
            alert.save(force_insert=True)
            created += 1
        except (ValueError, TypeError, IntegrityError) as error:
            invalid += 1
            logger.warning(
                "Skipping invalid %s alert %s: %s",
                normalized.source,
                normalized.source_alert_id,
                error,
            )
    return created, skipped, invalid


def initial_cursor() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=24)


def source_cursor(source_name: str) -> datetime:
    state = IngestionState.objects.filter(source=source_name).first()
    if state and state.last_success_at:
        return state.last_success_at
    return initial_cursor()


def mark_source_succeeded(source_name: str, completed_at: datetime) -> None:
    IngestionState.objects.update_or_create(
        source=source_name,
        defaults={"last_success_at": completed_at},
    )
