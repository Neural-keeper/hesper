from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterator

from alerts.types import NormalizedAlert


class SampleSource:
    """Provide deterministic synthetic alerts for local development."""

    name = "sample"

    def fetch(self, since: datetime) -> Iterator[NormalizedAlert]:
        observed_at = datetime.now(timezone.utc) - timedelta(hours=1)
        if observed_at <= since:
            return
        for identifier, ra, dec, magnitude, alert_class in (
            ("sample-orion", "83.8", "-5.4", "12.4", "supernova"),
            ("sample-southern", "120", "-70", "11.8", "nova"),
        ):
            yield NormalizedAlert(
                source=self.name,
                source_alert_id=identifier,
                observed_at=observed_at,
                received_at=datetime.now(timezone.utc),
                ra_deg=Decimal(ra),
                dec_deg=Decimal(dec),
                magnitude=Decimal(magnitude),
                band="r",
                alert_class=alert_class,
                class_confidence=Decimal("0.82"),
                raw={"sample": True, "identifier": identifier},
            )
