from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ObserverProfile


@pytest.fixture
def user(db: object) -> User:
    return get_user_model().objects.create_user(
        username="observer", password="test-password"
    )


def make_profile(user: User) -> ObserverProfile:
    return ObserverProfile(
        user=user,
        display_name="Night watcher",
        latitude=Decimal("27.9500"),
        longitude=Decimal("-82.4600"),
    )


@pytest.mark.django_db
def test_observer_profile_accepts_valid_values(user: User) -> None:
    profile = make_profile(user)

    profile.full_clean()

    assert profile.limiting_magnitude == Decimal("14")
    assert profile.theme == ObserverProfile.Theme.SYSTEM


@pytest.mark.django_db
def test_observer_profile_rejects_out_of_range_values(user: User) -> None:
    profile = make_profile(user)
    profile.latitude = Decimal("91")
    profile.min_altitude_deg = Decimal("81")
    profile.limiting_magnitude = Decimal("4")

    with pytest.raises(ValidationError) as error:
        profile.full_clean()

    assert {"latitude", "min_altitude_deg", "limiting_magnitude"} <= set(
        error.value.message_dict
    )


@pytest.mark.django_db
def test_observer_profile_rejects_unknown_interest(user: User) -> None:
    profile = make_profile(user)
    profile.interests = ["unknown"]

    with pytest.raises(ValidationError, match="Unknown interests"):
        profile.full_clean()


@pytest.mark.django_db
def test_observer_profile_accepts_constellation_and_star_interests(
    user: User,
) -> None:
    profile = ObserverProfile(
        user=user,
        display_name="Observer",
        latitude=Decimal("27.95"),
        longitude=Decimal("-82.46"),
        interests=["constellation:Orion", "star:Betelgeuse"],
    )

    profile.full_clean()


@pytest.mark.django_db
def test_observer_profile_rejects_malformed_interests(user: User) -> None:
    profile = make_profile(user)
    profile.interests = "supernova"

    with pytest.raises(ValidationError, match="Interests must be a list"):
        profile.full_clean()


@pytest.mark.django_db
def test_observer_profile_rejects_out_of_range_longitude_and_altitude(
    user: User,
) -> None:
    profile = make_profile(user)
    profile.longitude = Decimal("181")
    profile.min_altitude_deg = Decimal("-1")

    with pytest.raises(ValidationError) as error:
        profile.full_clean()

    assert {"longitude", "min_altitude_deg"} <= set(error.value.message_dict)
