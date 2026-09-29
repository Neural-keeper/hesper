from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class NormalizedAlert:
    source: str
    source_alert_id: str
    observed_at: datetime
    received_at: datetime
    ra_deg: Decimal
    dec_deg: Decimal
    magnitude: Decimal
    object_id: str | None = None
    magnitude_error: Decimal | None = None
    band: str = ""
    alert_class: str = ""
    class_confidence: Decimal | None = None
    cutout_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
