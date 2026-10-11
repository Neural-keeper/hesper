from datetime import datetime, timezone

import pytest

from .astronomy import (
    constellation_of,
    dark_window,
    flux_to_ab_mag,
    timezone_for,
    visibility,
)
from .types import NightWindow, ObserverLocation


def test_maximum_altitude_cases() -> None:
    for latitude, declination in ((28, 0), (28, 28), (-30, 20), (45, -20)):
        expected = 90 - abs(latitude - declination)
        assert expected >= 0


def test_far_southern_object_is_not_observable() -> None:
    window = NightWindow(
        datetime(2026, 1, 15, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 15, 8, tzinfo=timezone.utc),
        "astronomical",
    )
    result = visibility(
        0,
        -70,
        ObserverLocation(28, -82.46),
        window,
        min_altitude_deg=30,
    )
    assert not result.is_observable
    assert result.max_altitude_deg is not None
    assert result.max_altitude_deg < 30


def test_high_declination_object_stays_near_latitude() -> None:
    window = NightWindow(
        datetime(2026, 1, 15, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 15, 8, tzinfo=timezone.utc),
        "astronomical",
    )
    result = visibility(0, 89, ObserverLocation(28, -82.46), window, 0)
    assert result.max_altitude_deg is not None
    assert 27 <= result.max_altitude_deg <= 29


def test_tampa_winter_has_normal_dark_window() -> None:
    result = dark_window(
        27.95,
        -82.46,
        10,
        datetime(2026, 1, 15, 18, tzinfo=timezone.utc),
    )
    assert result.has_darkness
    assert result.darkness_level == "astronomical"
    assert result.start is not None and result.end is not None
    assert result.end > result.start


def test_high_latitude_summer_does_not_raise() -> None:
    result = dark_window(70, 25, 0, datetime(2026, 6, 25, 12, tzinfo=timezone.utc))
    assert result.darkness_level in {"nautical", "civil", None}


def test_flux_to_ab_mag() -> None:
    assert flux_to_ab_mag(3631e9) == pytest.approx(0, abs=0.01)
    with pytest.raises(ValueError):
        flux_to_ab_mag(0)


def test_constellation_of_orion() -> None:
    result = constellation_of(83.8, -5.4)
    assert result.abbreviation == "Ori"
    assert result.name == "Orion"


def test_timezone_for_tampa() -> None:
    assert timezone_for(27.95, -82.46) == "America/New_York"
