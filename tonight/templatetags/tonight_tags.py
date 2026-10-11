from __future__ import annotations

from datetime import datetime
from typing import cast
from zoneinfo import ZoneInfo

from django import template

register = template.Library()


@register.filter
def local_time(value: datetime | None, timezone: ZoneInfo) -> str:
    if value is None:
        return "Not available"
    return value.astimezone(timezone).strftime("%b %-d, %I:%M %p")


@register.filter
def utc_iso(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat().replace("+00:00", "Z")


@register.filter
def confidence_percent(value: object) -> str:
    if value is None:
        return "Unknown confidence"
    return f"{float(cast(str, value)) * 100:.0f}% confidence"


@register.filter
def title_class(value: object) -> str:
    if not value:
        return "Unclassified"
    return str(value).replace("_", " ").title()
