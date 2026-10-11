from dataclasses import dataclass

from alerts.models import Alert
from sky.types import ConstellationInfo, Visibility


@dataclass(frozen=True, slots=True)
class MatchedAlert:
    alert: Alert
    visibility: Visibility
    constellation: ConstellationInfo
