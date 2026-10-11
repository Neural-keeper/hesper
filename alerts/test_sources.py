import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.request import Request

from alerts.sources.alerce import AlerceSource

FIXTURE = Path(__file__).parent / "fixtures" / "alerce_sample.json"


class _Response:
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> Literal[False]:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_alerce_fixture_normalizes_detection() -> None:
    detection = json.loads(FIXTURE.read_text())[0]
    calls: list[tuple[str, float]] = []

    def opener(request: Request, timeout: float) -> _Response:
        calls.append((request.full_url, timeout))
        if "list_objects" in request.full_url:
            return _Response({"items": [{"oid": detection["oid"]}]})
        return _Response([detection])

    source = AlerceSource(opener=opener)
    alerts = list(
        source.fetch(datetime(2026, 6, 26, 0, 0, tzinfo=timezone.utc))
    )

    assert len(alerts) == 1
    assert alerts[0].source == "alerce"
    assert alerts[0].source_alert_id == str(detection["measurement_id"])
    assert alerts[0].band == "z"
    assert 20 < alerts[0].magnitude < 21
    assert len(calls) == 2
