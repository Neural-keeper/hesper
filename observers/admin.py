from django.contrib import admin

from .models import ObserverProfile


@admin.register(ObserverProfile)
class ObserverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "user",
        "latitude",
        "longitude",
        "timezone",
        "limiting_magnitude",
        "theme",
    )
    list_filter = ("theme", "timezone")
    search_fields = ("display_name", "user__username", "user__email")
