from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from alerts.models import Alert, IngestionState

logger = logging.getLogger(__name__)


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def database_health(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("Database health check failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def _database_size() -> int | None:
    if connection.vendor != "postgresql":
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_database_size(current_database())")
        row = cursor.fetchone()
    return int(row[0]) if row else None


@staff_member_required
def status(request: HttpRequest) -> HttpResponse:
    state = IngestionState.objects.order_by("-last_success_at").first()
    return render(
        request,
        "admin/status.html",
        {
            "alert_count": Alert.objects.count(),
            "last_success_at": state.last_success_at if state else None,
            "database_size_bytes": _database_size(),
            "alert_source": settings.ALERT_SOURCE,
        },
    )
