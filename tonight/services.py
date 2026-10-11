from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast

from django.core.cache import cache

from alerts.models import Alert
from lore.services import lore_for_position
from observers.models import (
    ALERT_INTERESTS,
    CONSTELLATION_INTEREST_PREFIX,
    STAR_INTEREST_PREFIX,
    ObserverProfile,
)
from sky import (
    ObserverLocation,
    constellation_of,
    dark_window,
    visibility,
)

from .types import MatchedAlert

CACHE_TIMEOUT_SECONDS = 10 * 60
LOOKBACK = timedelta(hours=48)


def _interest_matches(
    alert: Alert,
    interests: set[str],
    constellation_name: str,
    nearest_star_name: str | None,
) -> bool:
    if alert.alert_class in interests:
        return True
    if f"{CONSTELLATION_INTEREST_PREFIX}{constellation_name}" in interests:
        return True
    return nearest_star_name is not None and (
        f"{STAR_INTEREST_PREFIX}{nearest_star_name}" in interests
    )


def _cache_key(profile: ObserverProfile, now: datetime) -> str:
    timestamp = now.astimezone(timezone.utc).replace(second=0, microsecond=0)
    return f"tonight:matches:{profile.pk}:{timestamp.isoformat()}"


def match_alerts_for_observer(
    profile: ObserverProfile,
    now: datetime,
) -> list[MatchedAlert]:
    """Return recent alerts visible during this observer's current night."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    key = _cache_key(profile, now)
    cached = cache.get(key)
    if cached is not None:
        return cast(list[MatchedAlert], cached)

    current = now.astimezone(timezone.utc)
    window = dark_window(
        float(profile.latitude),
        float(profile.longitude),
        float(profile.elevation_m),
        current,
    )
    if not window.has_darkness:
        cache.set(key, [], CACHE_TIMEOUT_SECONDS)
        return []

    interests = set(profile.interests)
    alert_class_interests = interests & ALERT_INTERESTS
    candidates = Alert.objects.filter(
        observed_at__gte=current - LOOKBACK,
        observed_at__lte=current,
        magnitude__lte=profile.limiting_magnitude,
    )
    has_location_interests = any(
        item.startswith((CONSTELLATION_INTEREST_PREFIX, STAR_INTEREST_PREFIX))
        for item in interests
    )
    if alert_class_interests and not has_location_interests:
        candidates = candidates.filter(alert_class__in=alert_class_interests)
    location = ObserverLocation(
        latitude=float(profile.latitude),
        longitude=float(profile.longitude),
        elevation_m=float(profile.elevation_m),
    )
    matches: list[MatchedAlert] = []
    for alert in candidates:
        constellation = constellation_of(float(alert.ra_deg), float(alert.dec_deg))
        lore = lore_for_position(float(alert.ra_deg), float(alert.dec_deg))
        if not _interest_matches(
            alert,
            interests,
            constellation.name,
            lore.nearest_star.proper_name if lore.nearest_star else None,
        ):
            continue
        result = visibility(
            float(alert.ra_deg),
            float(alert.dec_deg),
            location,
            window,
            float(profile.min_altitude_deg),
        )
        if not result.is_observable or result.best_time is None:
            continue
        matches.append(
            MatchedAlert(
                alert=alert,
                visibility=result,
                constellation=constellation,
                lore=lore,
            )
        )
    matches.sort(key=lambda match: cast(datetime, match.visibility.best_time))
    cache.set(key, matches, CACHE_TIMEOUT_SECONDS)
    return matches
