from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, pi, radians, sin, sqrt

from sky import constellation_of

from .models import CulturalConstellation, Star

SEARCH_RADIUS_DEGREES = 10.0


@dataclass(frozen=True, slots=True)
class CulturalLore:
    culture_name: str
    constellation_name: str
    description: str
    source_url: str
    license: str


@dataclass(frozen=True, slots=True)
class LoreResult:
    iau_constellation: str
    nearest_star: Star | None
    cultural_lore: tuple[CulturalLore, ...]


def _angular_distance(
    ra_one: float, dec_one: float, ra_two: float, dec_two: float
) -> float:
    ra_delta = radians(ra_one - ra_two)
    dec_one_radians = radians(dec_one)
    dec_two_radians = radians(dec_two)
    haversine = (
        sin((dec_two_radians - dec_one_radians) / 2) ** 2
        + cos(dec_one_radians)
        * cos(dec_two_radians)
        * sin(ra_delta / 2) ** 2
    )
    return 2 * asin(min(1.0, sqrt(haversine))) * 180 / pi


def lore_for_position(ra: float, dec: float) -> LoreResult:
    iau = constellation_of(ra, dec)
    stars = list(
        Star.objects.filter(proper_name__isnull=False, magnitude__lt=6).only(
            "hip_number", "proper_name", "ra_deg", "dec_deg", "magnitude"
        )
    )
    distances = [
        (_angular_distance(ra, dec, star.ra_deg, star.dec_deg), star)
        for star in stars
    ]
    nearest = min(
        distances,
        default=(SEARCH_RADIUS_DEGREES + 1, None),
        key=lambda item: item[0],
    )
    nearest_star = nearest[1] if nearest[0] <= SEARCH_RADIUS_DEGREES else None

    cultural_lore: list[CulturalLore] = []
    for constellation in CulturalConstellation.objects.select_related("culture").all():
        figure_stars = Star.objects.filter(
            hip_number__in=constellation.stars, magnitude__lt=6
        ).only("ra_deg", "dec_deg")
        if any(
            _angular_distance(ra, dec, star.ra_deg, star.dec_deg)
            <= SEARCH_RADIUS_DEGREES
            for star in figure_stars
        ):
            cultural_lore.append(
                CulturalLore(
                    constellation.culture.name,
                    constellation.english_name or constellation.native_name,
                    constellation.description,
                    constellation.source_url,
                    constellation.license,
                )
            )
    return LoreResult(iau.name, nearest_star, tuple(cultural_lore))
