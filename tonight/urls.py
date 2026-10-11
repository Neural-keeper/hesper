from django.urls import path

from .views import TonightView

app_name = "tonight"

urlpatterns = [
    path("", TonightView.as_view(), name="index"),
]
