from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import cos, log10
from typing import cast

import astropy.units as u
from astroplan import Observer
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
    get_body,
    get_constellation,
)
from astropy.time import Time
from timezonefinder import TimezoneFinder

from .types import (
    ConstellationInfo,
    NightWindow,
    ObserverLocation,
    Visibility,
)

_DARKNESS_LEVELS = (
    ("astronomical", -18),
    ("nautical", -12),
    ("civil", -6),
)
_CONSTELLATION_ABBREVIATIONS = {
    "Andromeda": "And",
    "Antlia": "Ant",
    "Apus": "Aps",
    "Aquarius": "Aqr",
    "Aquila": "Aql",
    "Ara": "Ara",
    "Aries": "Ari",
    "Auriga": "Aur",
    "Boötes": "Boo",
    "Caelum": "Cae",
    "Camelopardalis": "Cam",
    "Cancer": "Cnc",
    "Canes Venatici": "CVn",
    "Canis Major": "CMa",
    "Canis Minor": "CMi",
    "Capricornus": "Cap",
    "Carina": "Car",
    "Cassiopeia": "Cas",
    "Centaurus": "Cen",
    "Cepheus": "Cep",
    "Cetus": "Cet",
    "Chamaeleon": "Cha",
    "Circinus": "Cir",
    "Columba": "Col",
    "Coma Berenices": "Com",
    "Corona Australis": "CrA",
    "Corona Borealis": "CrB",
    "Corvus": "Crv",
    "Crater": "Crt",
    "Crux": "Cru",
    "Cygnus": "Cyg",
    "Delphinus": "Del",
    "Dorado": "Dor",
    "Draco": "Dra",
    "Equuleus": "Equ",
    "Eridanus": "Eri",
    "Fornax": "For",
    "Gemini": "Gem",
    "Grus": "Gru",
    "Hercules": "Her",
    "Horologium": "Hor",
    "Hydra": "Hya",
    "Hydrus": "Hyi",
    "Indus": "Ind",
    "Lacerta": "Lac",
    "Leo": "Leo",
    "Leo Minor": "LMi",
    "Lepus": "Lep",
    "Libra": "Lib",
    "Lupus": "Lup",
    "Lynx": "Lyn",
    "Lyra": "Lyr",
    "Mensa": "Men",
    "Microscopium": "Mic",
    "Monoceros": "Mon",
    "Musca": "Mus",
    "Norma": "Nor",
    "Octans": "Oct",
    "Ophiuchus": "Oph",
    "Orion": "Ori",
    "Pavo": "Pav",
    "Pegasus": "Peg",
    "Perseus": "Per",
    "Phoenix": "Phe",
    "Pictor": "Pic",
    "Pisces": "Psc",
    "Piscis Austrinus": "PsA",
    "Puppis": "Pup",
    "Pyxis": "Pyx",
    "Reticulum": "Ret",
    "Sagitta": "Sge",
    "Sagittarius": "Sgr",
    "Scorpius": "Sco",
    "Sculptor": "Scl",
    "Scutum": "Sct",
    "Serpens": "Ser",
    "Sextans": "Sex",
    "Taurus": "Tau",
    "Telescopium": "Tel",
    "Triangulum": "Tri",
    "Triangulum Australe": "TrA",
    "Tucana": "Tuc",
    "Ursa Major": "UMa",
    "Ursa Minor": "UMi",
    "Vela": "Vel",
    "Virgo": "Vir",
    "Volans": "Vol",
    "Vulpecula": "Vul",
}


def _observer(location: ObserverLocation) -> Observer:
    earth_location = EarthLocation.from_geodetic(
        location.longitude * u.deg,
        location.latitude * u.deg,
        location.elevation_m * u.m,
    )
    return Observer(location=earth_location, name="observer", timezone="UTC")


def _utc_datetime(value: Time) -> datetime:
    return cast(datetime, value.to_datetime(timezone=timezone.utc))


def dark_window(
    lat: float,
    lon: float,
    elevation_m: float,
    now: datetime,
) -> NightWindow:
    """Find tonight's dark interval, falling back to lighter twilight if needed."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = now.astimezone(timezone.utc)
    observer = _observer(ObserverLocation(lat, lon, elevation_m))
    for level, horizon in _DARKNESS_LEVELS:
        intervals: list[tuple[datetime, datetime]] = []
        anchor = current - timedelta(days=2)
        for day in range(5):
            try:
                event_name = {
                    -18: "astronomical",
                    -12: "nautical",
                    -6: "civil",
                }[horizon]
                evening_method = getattr(observer, f"twilight_evening_{event_name}")
                morning_method = getattr(observer, f"twilight_morning_{event_name}")
                evening = evening_method(
                    Time(anchor + timedelta(days=day)), which="next"
                )
                morning = morning_method(evening + 1 * u.min, which="next")
            except (ValueError, TypeError, IndexError):
                continue
            start, end = _utc_datetime(evening), _utc_datetime(morning)
            if end > start:
                intervals.append((start, end))
        containing = next(
            ((start, end) for start, end in intervals if start <= current <= end),
            None,
        )
        if containing is not None:
            return NightWindow(*containing, darkness_level=level)
        upcoming = next(
            ((start, end) for start, end in intervals if start > current),
            None,
        )
        if upcoming is not None:
            return NightWindow(*upcoming, darkness_level=level)
    return NightWindow(None, None, None)


def visibility(
    ra: float,
    dec: float,
    observer_location: ObserverLocation,
    window: NightWindow,
    min_altitude_deg: float,
    sampling_minutes: int = 10,
) -> Visibility:
    """Sample a target through the night and measure when it clears the limit."""
    if sampling_minutes <= 0:
        raise ValueError("sampling_minutes must be positive")
    if not window.has_darkness:
        return Visibility(False, None, None, None, None, None, None)
    assert window.start is not None and window.end is not None
    total_seconds = (window.end - window.start).total_seconds()
    count = max(1, int(total_seconds // (sampling_minutes * 60)))
    times = [
        window.start + (window.end - window.start) * index / count
        for index in range(count + 1)
    ]
    astropy_times = Time(times)
    location = EarthLocation.from_geodetic(
        observer_location.longitude * u.deg,
        observer_location.latitude * u.deg,
        observer_location.elevation_m * u.m,
    )
    frame = AltAz(obstime=astropy_times, location=location)
    target = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    altitudes = target.transform_to(frame).alt.deg
    observable = [altitude >= min_altitude_deg for altitude in altitudes]
    best_index = max(range(len(altitudes)), key=lambda index: altitudes[index])
    best_time = times[best_index]
    first = next((index for index, value in enumerate(observable) if value), None)
    last = next(
        (index for index in range(len(observable) - 1, -1, -1) if observable[index]),
        None,
    )
    moon = get_body("moon", astropy_times, location=location)
    separation = target.separation(moon).deg[best_index]
    moon_at_best = get_body("moon", Time(best_time), location=location)
    sun_at_best = get_body("sun", Time(best_time), location=location)
    elongation = moon_at_best.separation(sun_at_best).rad
    illumination = (1 - cos(float(elongation))) / 2
    return Visibility(
        first is not None,
        best_time,
        float(altitudes[best_index]),
        times[first] if first is not None else None,
        times[last] if last is not None else None,
        float(separation),
        illumination,
    )


def constellation_of(ra: float, dec: float) -> ConstellationInfo:
    """Return the IAU constellation containing the supplied sky coordinates."""
    name = str(get_constellation(SkyCoord(ra=ra * u.deg, dec=dec * u.deg)))
    return ConstellationInfo(_CONSTELLATION_ABBREVIATIONS[name], name)


def flux_to_ab_mag(flux_njy: float) -> float:
    """Convert positive nanojansky flux into the astronomical AB magnitude scale."""
    if flux_njy <= 0:
        raise ValueError("flux_njy must be greater than zero")
    return -2.5 * log10(flux_njy) + 31.4


def timezone_for(lat: float, lon: float) -> str:
    """Return the IANA timezone containing the supplied geographic coordinates."""
    timezone_name = TimezoneFinder().timezone_at(lat=lat, lng=lon)
    if timezone_name is None:
        raise ValueError("No timezone found for these coordinates")
    return timezone_name
