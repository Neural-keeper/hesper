import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_returns_200_and_contains_heading(client: Client) -> None:
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert response.context["view"].template_name == "core/home.html"
    assert b"<h1>hesper</h1>" in response.content
