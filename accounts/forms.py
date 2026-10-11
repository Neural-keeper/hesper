from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from lore.models import CulturalConstellation, Star
from observers.models import ObserverProfile
from sky import timezone_for


class SignUpForm(UserCreationForm):  # type: ignore[type-arg]
    email = forms.EmailField(
        required=True,
        help_text="Used only for password reset emails.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ObserverProfileForm(forms.ModelForm):  # type: ignore[type-arg]
    @staticmethod
    def _interest_choices() -> list[tuple[str, str]]:
        alert_choices = [
            ("supernova", "Supernova"),
            ("variable_star", "Variable star"),
            ("nova", "Nova"),
            ("asteroid", "Asteroid"),
            ("other", "Other"),
        ]
        constellation_choices = [
            (
                f"constellation:{constellation.native_name}",
                str(constellation.english_name or constellation.native_name or ""),
            )
            for constellation in CulturalConstellation.objects.filter(
                culture__name="Modern (IAU)"
            ).order_by("english_name", "native_name")
        ]
        star_choices = [
            (f"star:{star.proper_name}", str(star.proper_name))
            for star in Star.objects.filter(proper_name__isnull=False)
            .exclude(proper_name="")
            .order_by("proper_name")
        ]
        return alert_choices + [
            (value, label or "") for value, label in constellation_choices
        ] + star_choices

    interests = forms.MultipleChoiceField(
        choices=(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ObserverProfile
        fields = (
            "display_name",
            "latitude",
            "longitude",
            "elevation_m",
            "limiting_magnitude",
            "interests",
            "theme",
        )
        widgets = {
            "latitude": forms.NumberInput(
                attrs={
                    "step": "0.0001",
                    "min": "-90",
                    "max": "90",
                    "placeholder": "27.9500",
                    "aria-describedby": "id_latitude_help id_latitude_error",
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "step": "0.0001",
                    "min": "-180",
                    "max": "180",
                    "placeholder": "-82.4600",
                    "aria-describedby": "id_longitude_help id_longitude_error",
                }
            ),
            "elevation_m": forms.NumberInput(attrs={"step": "0.1"}),
            "limiting_magnitude": forms.NumberInput(
                attrs={
                    "step": "0.1",
                    "min": "5",
                    "max": "20",
                    "aria-describedby": "id_limiting_magnitude_help",
                }
            ),
        }
        help_texts = {
            "latitude": "Decimal degrees north or south. Example: 27.9500.",
            "longitude": "Decimal degrees east or west. Example: -82.4600.",
            "elevation_m": "Optional height above sea level in metres.",
            "limiting_magnitude": (
                "Typical values: naked eye about 6; binoculars about 9; "
                "small telescope 11 to 13; telescope with a camera 15 or more."
            ),
            "interests": "Choose the alert classes you want to see.",
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        interests = self.fields["interests"]
        assert isinstance(interests, forms.MultipleChoiceField)
        interests.choices = self._interest_choices()
        if self.instance.pk:
            self.initial["interests"] = self.instance.interests
        for name, field in self.fields.items():
            described_by = [f"id_{name}_help"]
            if self.errors.get(name):
                described_by.append(f"id_{name}_error")
            field.widget.attrs["aria-describedby"] = " ".join(described_by)

    def clean(self) -> dict[str, object]:
        cleaned = super().clean() or {}
        latitude = cleaned.get("latitude")
        longitude = cleaned.get("longitude")
        if latitude is not None and longitude is not None:
            try:
                cleaned["timezone"] = timezone_for(float(latitude), float(longitude))
            except ValueError as error:
                raise forms.ValidationError(
                    f"We could not determine a time zone: {error}"
                ) from error
        return cast(dict[str, object], cleaned)

    def save(self, commit: bool = True) -> ObserverProfile:
        profile = super().save(commit=False)
        profile.timezone = self.cleaned_data["timezone"]
        if commit:
            profile.save()
        return cast(ObserverProfile, profile)
