from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from lore.models import CulturalConstellation, SkyCulture, Star
from observers.models import ObserverProfile


@pytest.mark.django_db
def test_signup_leads_to_onboarding(client: Client) -> None:
    response = client.post(
        reverse("accounts:signup"),
        {
            "username": "new-observer",
            "email": "new@example.com",
            "password1": "A-long-password-123!",
            "password2": "A-long-password-123!",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:onboarding")
    assert client.session.get("_auth_user_id") is not None


@pytest.mark.django_db
def test_onboarding_leads_to_tonight_and_derives_timezone(client: Client) -> None:
    user = get_user_model().objects.create_user(
        username="setup", password="secret", email="setup@example.com"
    )
    client.force_login(user)

    response = client.post(
        reverse("accounts:onboarding"),
        {
            "display_name": "Setup observer",
            "latitude": "27.9500",
            "longitude": "-82.4600",
            "elevation_m": "10",
            "limiting_magnitude": "14",
            "interests": ["supernova"],
            "theme": "night-red",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("tonight:index")
    profile = ObserverProfile.objects.get(user=user)
    assert profile.timezone == "America/New_York"
    assert profile.theme == "night-red"


@pytest.mark.django_db
def test_invalid_coordinates_have_accessible_errors(client: Client) -> None:
    user = get_user_model().objects.create_user(username="invalid", password="secret")
    client.force_login(user)

    response = client.post(
        reverse("accounts:onboarding"),
        {
            "display_name": "Invalid",
            "latitude": "91",
            "longitude": "-181",
            "limiting_magnitude": "14",
            "theme": "system",
        },
    )

    assert response.status_code == 200
    assert b"form-errors" in response.content
    assert b'href="#id_latitude"' in response.content
    assert b'href="#id_longitude"' in response.content
    assert b"id_latitude_error" in response.content


@pytest.mark.django_db
def test_theme_is_applied_in_rendered_html(client: Client) -> None:
    user = get_user_model().objects.create_user(username="theme", password="secret")
    ObserverProfile.objects.create(
        user=user,
        display_name="Theme tester",
        latitude=Decimal("27.95"),
        longitude=Decimal("-82.46"),
        theme="dark",
    )
    client.force_login(user)

    response = client.get(reverse("core:home"))

    assert b'<html lang="en" data-theme="dark">' in response.content


@pytest.mark.django_db
def test_profile_form_lists_constellations_and_named_stars() -> None:
    from .forms import ObserverProfileForm

    culture = SkyCulture.objects.create(
        name="Modern (IAU)",
        region_or_people="World",
        description="Modern lore",
        source_url="https://example.com/modern",
        license="CC BY-SA 4.0",
        credit_text="Stellarium's team",
    )
    CulturalConstellation.objects.create(
        culture=culture,
        native_name="Orion",
        english_name="Orion",
        description="The hunter",
        stars=[],
        source_url="https://example.com/orion",
        license="CC BY-SA 4.0",
    )
    Star.objects.create(
        hip_number=27989,
        proper_name="Betelgeuse",
        ra_deg=88.79,
        dec_deg=7.4,
        magnitude=0.5,
    )

    choices = dict(ObserverProfileForm().fields["interests"].choices)

    assert choices["constellation:Orion"] == "Orion"
    assert choices["star:Betelgeuse"] == "Betelgeuse"
