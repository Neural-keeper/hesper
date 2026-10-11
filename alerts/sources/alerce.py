from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from alerts.types import NormalizedAlert
from sky.astronomy import flux_to_ab_mag

logger = logging.getLogger(__name__)

_MJD_EPOCH = datetime(1858, 11, 17, tzinfo=timezone.utc)


def _mjd_to_datetime(mjd: float) -> datetime:
    return _MJD_EPOCH + timedelta(days=mjd)


class AlerceSource:
    """Read recent LSST alerts from ALeRCE's free public API."""

    name = "alerce"

    def __init__(
        self,
        *,
        base_url: str = "https://api-lsst.alerce.online",
        timeout: float = 20,
        max_objects: int = 25,
        max_retries: int = 2,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_objects = max_objects
        self.max_retries = max_retries
        self._opener = opener

    def _get_json(self, path: str, params: dict[str, str]) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json"})
        for attempt in range(self.max_retries + 1):
            try:
                with self._opener(request, timeout=self.timeout) as response:
                    return json.load(response)
            except (HTTPError, URLError, TimeoutError) as error:
                if attempt == self.max_retries:
                    raise
                delay = 2**attempt
                logger.warning(
                    "ALeRCE request failed (%s); retrying in %s seconds",
                    error,
                    delay,
                )
                time.sleep(delay)

    def fetch(self, since: datetime) -> Iterator[NormalizedAlert]:
        """Yield LSST detections newer than ``since`` from a bounded API page."""
        since_utc = since.astimezone(timezone.utc)
        since_mjd = (since_utc - _MJD_EPOCH).total_seconds() / 86400
        objects = self._get_json(
            "object_api/list_objects",
            {
                "survey": "lsst",
                "lastmjd": str(since_mjd),
                "page": "1",
                "page_size": str(self.max_objects),
            },
        )
        for obj in objects.get("items", []):
            oid = str(obj["oid"])
            detections = self._get_json(
                "lightcurve_api/detections",
                {"survey_id": "lsst", "oid": oid},
            )
            for detection in detections:
                mjd = float(detection["mjd"])
                observed_at = _mjd_to_datetime(mjd)
                if observed_at <= since_utc:
                    continue
                flux = detection.get("psfFlux")
                if flux is None or flux <= 0:
                    logger.warning(
                        "Skipping ALeRCE detection %s with invalid flux", oid
                    )
                    continue
                # ALeRCE documents psfFlux as an LSST nJy PSF-flux measurement.
                # Convert that positive flux to an AB magnitude for Hesper.
                magnitude = Decimal(str(flux_to_ab_mag(float(flux))))
                flux_error = detection.get("psfFluxErr")
                magnitude_error = None
                if flux_error is not None and flux_error > 0:
                    magnitude_error = Decimal(
                        str(1.085736 * float(flux_error) / float(flux))
                    )
                band = detection.get("band_name")
                if band is None:
                    band = detection.get("band_map", {}).get(str(detection.get("band")))
                yield NormalizedAlert(
                    source=self.name,
                    source_alert_id=str(detection["measurement_id"]),
                    object_id=oid,
                    observed_at=observed_at,
                    received_at=datetime.now(timezone.utc),
                    ra_deg=Decimal(str(detection["ra"])),
                    dec_deg=Decimal(str(detection["dec"])),
                    magnitude=magnitude,
                    magnitude_error=magnitude_error,
                    band=band,
                    raw=detection,
                )
