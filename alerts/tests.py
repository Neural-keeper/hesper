from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Alert
from .types import NormalizedAlert


def make_alert(source_alert_id="alert-1"):
    return Alert(
        source="sample",
        source_alert_id=source_alert_id,
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
        ra_deg=Decimal("83.8000"),
        dec_deg=Decimal("-5.4000"),
        magnitude=Decimal("14.200"),
    )


@pytest.mark.django_db
def test_alert_accepts_valid_values():
    alert = make_alert()

    alert.full_clean()
    alert.save()

    assert str(alert) == "sample:alert-1"


@pytest.mark.django_db
def test_alert_rejects_out_of_range_coordinates_and_confidence():
    alert = make_alert()
    alert.ra_deg = Decimal("361")
    alert.dec_deg = Decimal("-91")
    alert.class_confidence = Decimal("1.1")

    with pytest.raises(ValidationError) as error:
        alert.full_clean()

    assert {"ra_deg", "dec_deg", "class_confidence"} <= set(
        error.value.message_dict
    )


@pytest.mark.django_db
def test_alert_source_and_id_are_unique():
    make_alert().save()

    with pytest.raises(IntegrityError):
        make_alert().save()



def test_normalized_alert_is_frozen():
    alert = NormalizedAlert(
        source="sample",
        source_alert_id="alert-1",
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ra_deg=Decimal("83.8"),
        dec_deg=Decimal("-5.4"),
        magnitude=Decimal("14.2"),
    )

    with pytest.raises(AttributeError):
        alert.magnitude = Decimal("13")
