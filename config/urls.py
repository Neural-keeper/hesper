from django.contrib import admin
from django.urls import include, path

from .views import database_health, health, status

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", health, name="health"),
    path("healthz/db", database_health, name="database-health"),
    path("admin/status/", status, name="status"),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
    path("tonight/", include("tonight.urls")),
]
