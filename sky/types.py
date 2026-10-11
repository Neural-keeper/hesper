from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ObserverLocation:
    latitude: float
    longitude: float
    elevation_m: float = 0.0


@dataclass(frozen=True, slots=True)
class NightWindow:
    start: datetime | None
    end: datetime | None
    darkness_level: str | None

    @property
    def has_darkness(self) -> bool:
        return self.start is not None and self.end is not None


@dataclass(frozen=True, slots=True)
class Visibility:
    is_observable: bool
    best_time: datetime | None
    max_altitude_deg: float | None
    observable_from: datetime | None
    observable_until: datetime | None
    moon_separation_deg: float | None
    moon_illumination: float | None


@dataclass(frozen=True, slots=True)
class ConstellationInfo:
    abbreviation: str
    name: str
