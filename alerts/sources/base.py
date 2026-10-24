from datetime import datetime
from typing import Iterable, Protocol

from alerts.types import NormalizedAlert


class AlertSource(Protocol):
    """Interface implemented by every alert broker integration."""

    name: str

    def fetch(self, since: datetime) -> Iterable[NormalizedAlert]:
        """Yield alerts observed after ``since``."""
