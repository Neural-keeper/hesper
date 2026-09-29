from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "source_alert_id",
        "observed_at",
        "alert_class",
        "magnitude",
        "band",
        "dec_deg",
    )
    list_filter = ("source", "alert_class", "band")
    search_fields = ("source_alert_id", "object_id", "alert_class")
    date_hierarchy = "observed_at"
