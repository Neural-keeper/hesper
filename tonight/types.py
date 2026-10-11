from dataclasses import dataclass

from alerts.models import Alert
from lore.services import LoreResult
from sky.types import ConstellationInfo, Visibility


@dataclass(frozen=True, slots=True)
class MatchedAlert:
    alert: Alert
    visibility: Visibility
    constellation: ConstellationInfo
    lore: LoreResult | None = None
