from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from alerts.models import Alert
from lore.models import Star
from lore.services import LoreResult
from observers.models import ObserverProfile
from sky.types import ConstellationInfo, NightWindow, Visibility

from .services import match_alerts_for_observer
from .templatetags.tonight_tags import interest_label
from .types import MatchedAlert

NOW = datetime(2026, 1, 15, 18, tzinfo=timezone.utc)


@pytest.fixture
def profile(db: object) -> ObserverProfile:
    user = get_user_model().objects.create_user(username="tonight", password="secret")
    return ObserverProfile.objects.create(
        user=user,
        display_name="Tonight tester",
        latitude=Decimal("27.95"),
        longitude=Decimal("-82.46"),
        timezone="America/New_York",
        interests=["supernova", "nova"],
        limiting_magnitude=Decimal("14"),
    )


def create_alert(
    identifier: str,
    *,
    alert_class: str = "supernova",
    magnitude: str = "12",
    dec: str = "-5",
    ra: str = "83.8",
) -> Alert:
    return Alert.objects.create(
        source="test",
        source_alert_id=identifier,
        observed_at=NOW.replace(hour=12),
        received_at=NOW,
        ra_deg=Decimal(ra),
        dec_deg=Decimal(dec),
        magnitude=Decimal(magnitude),
        alert_class=alert_class,
        class_confidence=Decimal("0.82"),
    )


def fake_window() -> NightWindow:
    return NightWindow(
        datetime(2026, 1, 15, 23, tzinfo=timezone.utc),
        datetime(2026, 1, 16, 11, tzinfo=timezone.utc),
        "astronomical",
    )


def fake_visibility(best_hour: int) -> Visibility:
    best_time = datetime(2026, 1, 16, best_hour, tzinfo=timezone.utc)
    return Visibility(
        True,
        best_time,
        60,
        best_time,
        best_time,
        40,
        0.5,
    )


@pytest.mark.django_db
def test_matching_filters_interests_and_magnitude_and_sorts(
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = create_alert("first")
    create_alert("faint", magnitude="15")
    create_alert("wrong-class", alert_class="asteroid")
    create_alert("second", alert_class="nova", ra="84")

    monkeypatch.setattr("tonight.services.dark_window", lambda *args: fake_window())
    monkeypatch.setattr(
        "tonight.services.visibility",
        lambda ra, dec, location, window, minimum: fake_visibility(
            1 if ra == float(first.ra_deg) else 3
        ),
    )
    monkeypatch.setattr(
        "tonight.services.constellation_of",
        lambda ra, dec: ConstellationInfo("Ori", "Orion"),
    )
    cache.clear()

    matches = match_alerts_for_observer(profile, NOW)

    assert [match.alert.source_alert_id for match in matches] == ["first", "second"]


@pytest.mark.django_db
def test_matching_supports_constellation_and_named_star_interests(
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile.interests = ["constellation:Orion", "star:Betelgeuse"]
    profile.save(update_fields=["interests"])
    first = create_alert("orion")
    create_alert("other", ra="120")
    betelgeuse = Star.objects.create(
        hip_number=27989,
        proper_name="Betelgeuse",
        ra_deg=88.79,
        dec_deg=7.4,
        magnitude=0.5,
    )

    monkeypatch.setattr("tonight.services.dark_window", lambda *args: fake_window())
    monkeypatch.setattr("tonight.services.visibility", lambda *args: fake_visibility(1))
    monkeypatch.setattr(
        "tonight.services.constellation_of",
        lambda ra, dec: ConstellationInfo("Ori", "Orion")
        if ra == float(first.ra_deg)
        else ConstellationInfo("And", "Andromeda"),
    )
    monkeypatch.setattr(
        "tonight.services.lore_for_position",
        lambda ra, dec: LoreResult(
            "Orion",
            betelgeuse
            if ra == float(first.ra_deg)
            else None,
            (),
        ),
    )
    cache.clear()

    matches = match_alerts_for_observer(profile, NOW)

    assert [match.alert.source_alert_id for match in matches] == ["orion"]


def test_interest_label_formats_named_constellations_and_stars() -> None:
    assert interest_label("constellation:Orion") == "Orion"
    assert interest_label("star:Betelgeuse") == "Betelgeuse"
    assert interest_label("variable_star") == "Variable Star"


@pytest.mark.django_db
def test_matching_cache_avoids_recomputing(
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_alert("cached")
    calls = 0

    def count_visibility(*args: object) -> Visibility:
        nonlocal calls
        calls += 1
        return fake_visibility(1)

    monkeypatch.setattr("tonight.services.dark_window", lambda *args: fake_window())
    monkeypatch.setattr("tonight.services.visibility", count_visibility)
    monkeypatch.setattr(
        "tonight.services.constellation_of",
        lambda ra, dec: ConstellationInfo("Ori", "Orion"),
    )
    cache.clear()

    match_alerts_for_observer(profile, NOW)
    match_alerts_for_observer(profile, NOW)

    assert calls == 1


@pytest.mark.django_db
def test_page_requires_login(client: Client) -> None:
    response = client.get(reverse("tonight:index"))

    assert response.status_code == 302
    assert "login" in response["Location"]


@pytest.mark.django_db
def test_page_renders_empty_state_for_user_with_no_matches(
    client: Client,
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client.force_login(profile.user)
    monkeypatch.setattr(
        "tonight.views.match_alerts_for_observer",
        lambda profile, now: [],
    )
    monkeypatch.setattr("tonight.views.dark_window", lambda *args: fake_window())
    monkeypatch.setattr(
        "tonight.views.visibility",
        lambda *args: fake_visibility(1),
    )

    response = client.get(reverse("tonight:index"))

    assert response.status_code == 200
    assert b"Nothing brighter than magnitude" in response.content
    assert b'aria-live="polite"' in response.content


@pytest.mark.django_db
def test_page_filters_named_constellation_and_star_interests(
    client: Client,
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile.interests = ["constellation:Orion", "star:Betelgeuse"]
    profile.save(update_fields=["interests"])
    client.force_login(profile.user)
    orion_match = MatchedAlert(
        alert=create_alert("orion"),
        visibility=fake_visibility(1),
        constellation=ConstellationInfo("Ori", "Orion"),
        lore=LoreResult(
            "Orion",
            Star.objects.create(
                hip_number=27989,
                proper_name="Betelgeuse",
                ra_deg=88.79,
                dec_deg=7.4,
                magnitude=0.5,
            ),
            (),
        ),
    )
    andromeda_match = MatchedAlert(
        alert=create_alert("andromeda", ra="120", dec="40"),
        visibility=fake_visibility(2),
        constellation=ConstellationInfo("And", "Andromeda"),
        lore=LoreResult("Andromeda", None, ()),
    )
    monkeypatch.setattr(
        "tonight.views.match_alerts_for_observer",
        lambda profile, now: [orion_match, andromeda_match],
    )
    monkeypatch.setattr("tonight.views.dark_window", lambda *args: fake_window())
    monkeypatch.setattr("tonight.views.visibility", lambda *args: fake_visibility(1))

    response = client.get(reverse("tonight:index"), {"class": "constellation:Orion"})

    assert response.status_code == 200
    assert b"Orion" in response.content
    assert b"Andromeda" not in response.content


@pytest.mark.django_db
def test_page_returns_match_fragment_for_htmx_request(
    client: Client,
    profile: ObserverProfile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client.force_login(profile.user)
    alert = create_alert("fragment")
    match = MatchedAlert(
        alert=alert,
        visibility=fake_visibility(1),
        constellation=ConstellationInfo("Ori", "Orion"),
    )
    monkeypatch.setattr(
        "tonight.views.match_alerts_for_observer",
        lambda profile, now: [match],
    )
    monkeypatch.setattr("tonight.views.dark_window", lambda *args: fake_window())
    monkeypatch.setattr(
        "tonight.views.visibility",
        lambda *args: fake_visibility(1),
    )

    response = client.get(
        reverse("tonight:index"),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert b"Observable alerts" in response.content
    assert b"site-header" not in response.content
