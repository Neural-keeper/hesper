from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from observers.models import ObserverProfile
from sky import ObserverLocation, dark_window, visibility

from .services import match_alerts_for_observer


class TonightView(LoginRequiredMixin, View):
    template_name = "tonight/index.html"
    partial_template_name = "tonight/_matches.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        profile = get_object_or_404(ObserverProfile, user=request.user)
        now = datetime.now(timezone.utc)
        matches = match_alerts_for_observer(profile, now)
        selected_class = request.GET.get("class", "").strip()
        maximum_magnitude = request.GET.get("max_magnitude", "").strip()
        filtered_matches = [
            match
            for match in matches
            if not selected_class or match.alert.alert_class == selected_class
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
        }
        template = (
            self.partial_template_name
            if request.headers.get("HX-Request") == "true"
            else self.template_name
        )
        return render(request, template, context)
