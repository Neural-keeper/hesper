from typing import cast

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from observers.models import ObserverProfile

from .forms import ObserverProfileForm, SignUpForm


class SignUpView(CreateView):  # type: ignore[type-arg]
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:onboarding")

    def form_valid(self, form: SignUpForm) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class AccountLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self) -> str:
        if not hasattr(self.request.user, "observer_profile"):
            return str("/accounts/onboarding/")
        return super().get_success_url()


def _profile_for_form(request: HttpRequest) -> ObserverProfile:
    user = cast(User, request.user)
    try:
        return user.observer_profile
    except ObserverProfile.DoesNotExist:
        return ObserverProfile(
            user=user,
            display_name=user.get_username(),
        )


@login_required
def onboarding(request: HttpRequest) -> HttpResponse:
    profile = _profile_for_form(request)
    if request.method == "POST":
        form = ObserverProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("tonight:index")
    else:
        form = ObserverProfileForm(instance=profile)
    return render(
        request,
        "accounts/profile_form.html",
        {"form": form, "page_title": "Set up your observing profile"},
    )


@login_required
def settings(request: HttpRequest) -> HttpResponse:
    profile = _profile_for_form(request)
    if request.method == "POST":
        form = ObserverProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("accounts:settings")
    else:
        form = ObserverProfileForm(instance=profile)
    return render(
        request,
        "accounts/profile_form.html",
        {"form": form, "page_title": "Observer settings"},
    )
