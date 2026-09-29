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
def test_observer_profile_accepts_valid_values(user):
    profile = make_profile(user)

    profile.full_clean()

    assert profile.limiting_magnitude == Decimal("14")
    assert profile.theme == ObserverProfile.Theme.SYSTEM


@pytest.mark.django_db
def test_observer_profile_rejects_out_of_range_values(user):
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
def test_observer_profile_rejects_unknown_interest(user):
    profile = make_profile(user)
    profile.interests = ["unknown"]

    with pytest.raises(ValidationError, match="Unknown interests"):
        profile.full_clean()
