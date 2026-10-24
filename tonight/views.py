from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from lore.models import SkyCulture
from observers.models import (
    ALERT_INTERESTS,
    CONSTELLATION_INTEREST_PREFIX,
    STAR_INTEREST_PREFIX,
    ObserverProfile,
)
from sky import ObserverLocation, dark_window, visibility

from .services import match_alerts_for_observer
from .types import MatchedAlert


class TonightView(LoginRequiredMixin, View):
    template_name = "tonight/index.html"
    partial_template_name = "tonight/_matches.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        profile = get_object_or_404(ObserverProfile, user=request.user)
        now = datetime.now(timezone.utc)
        matches = match_alerts_for_observer(profile, now)
        selected_class = request.GET.get("class", "").strip()
        maximum_magnitude = request.GET.get("max_magnitude", "").strip()

        def matches_selected_interest(match: MatchedAlert) -> bool:
            if not selected_class:
                return True
            if selected_class in ALERT_INTERESTS:
                return match.alert.alert_class == selected_class
            if selected_class.startswith(CONSTELLATION_INTEREST_PREFIX):
                target = selected_class.removeprefix(CONSTELLATION_INTEREST_PREFIX)
                return match.constellation.name == target
            if selected_class.startswith(STAR_INTEREST_PREFIX):
                target = selected_class.removeprefix(STAR_INTEREST_PREFIX)
                nearest_star = (
                    getattr(match.lore, "nearest_star", None)
                    if match.lore
                    else None
                )
                if nearest_star is None:
                    return False
                nearest_star_name = getattr(nearest_star, "proper_name", None)
                return (
                    isinstance(nearest_star_name, str)
                    and nearest_star_name == target
                )
            return False

        filtered_matches = [
            match for match in matches if matches_selected_interest(match)
        ]
        if maximum_magnitude:
            try:
                limit = float(maximum_magnitude)
            except ValueError:
                limit = None
            if limit is not None:
                filtered_matches = [
                    match
                    for match in filtered_matches
                    if float(match.alert.magnitude) <= limit
                ]

        try:
            local_timezone = ZoneInfo(profile.timezone)
        except ZoneInfoNotFoundError as error:
            raise ImproperlyConfigured(
                f"Observer has an invalid IANA timezone: {profile.timezone}"
            ) from error
        window = dark_window(
            float(profile.latitude),
            float(profile.longitude),
            float(profile.elevation_m),
            now,
        )
        moon_illumination = None
        if window.has_darkness:
            moon_illumination = visibility(
                0,
                float(profile.latitude),
                ObserverLocation(
                    float(profile.latitude),
                    float(profile.longitude),
                    float(profile.elevation_m),
                ),
                window,
                -90,
            ).moon_illumination
        context = {
            "profile": profile,
            "matches": filtered_matches,
            "all_matches_count": len(matches),
            "window": window,
            "moon_illumination": moon_illumination,
            "local_timezone": local_timezone,
            "selected_class": selected_class,
            "maximum_magnitude": maximum_magnitude,
            "interest_choices": sorted(profile.interests),
            "lore_credits": SkyCulture.objects.exclude(credit_text="").order_by("name"),
            "lore_catalog_credit": (
                "Astronexus / David Nash and the HYG project. "
                "Licensed under CC BY-SA 4.0."
            ),
        }
        template = (
            self.partial_template_name
            if request.headers.get("HX-Request") == "true"
            else self.template_name
        )
        return render(request, template, context)
