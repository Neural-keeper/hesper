import pytest
from django.core.management import call_command

from .models import CulturalConstellation, SkyCulture, Star
from .services import lore_for_position


@pytest.mark.django_db
def test_import_lore_is_idempotent() -> None:
    call_command("import_lore")
    first_counts = (
        SkyCulture.objects.count(),
        Star.objects.count(),
        CulturalConstellation.objects.count(),
    )

    call_command("import_lore")

    assert (
        SkyCulture.objects.count(),
        Star.objects.count(),
        CulturalConstellation.objects.count(),
    ) == first_counts


@pytest.mark.django_db
def test_lore_near_betelgeuse_returns_iau_star_and_culture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    culture = SkyCulture.objects.create(
        name="Test culture",
        region_or_people="Test people",
        description="Culture source",
        source_url="https://example.com/culture",
        license="CC BY 4.0",
        credit_text="Test credit",
    )
    Star.objects.create(
        hip_number=27989,
        proper_name="Betelgeuse",
        ra_deg=88.792935,
        dec_deg=7.407063,
        magnitude=0.5,
    )
    CulturalConstellation.objects.create(
        culture=culture,
        native_name="Test Orion",
        english_name="Test Orion",
        description="Source description",
        stars=[27989],
        source_url="https://example.com/constellation",
        license="CC BY 4.0",
    )
    monkeypatch.setattr(
        "lore.services.constellation_of",
        lambda ra, dec: type("Constellation", (), {"name": "Orion"})(),
    )

    result = lore_for_position(88.792935, 7.407063)

    assert result.iau_constellation == "Orion"
    assert result.nearest_star is not None
    assert result.nearest_star.proper_name == "Betelgeuse"
    assert [item.constellation_name for item in result.cultural_lore] == ["Test Orion"]


@pytest.mark.django_db
def test_lore_far_from_named_star_returns_only_iau_constellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "lore.services.constellation_of",
        lambda ra, dec: type("Constellation", (), {"name": "Sextans"})(),
    )

    result = lore_for_position(157.6395, -0.7538)

    assert result.iau_constellation == "Sextans"
    assert result.nearest_star is None
    assert result.cultural_lore == ()
