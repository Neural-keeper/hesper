from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from alerts.services import (
    get_source,
    ingest,
    mark_source_succeeded,
    source_cursor,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch alerts from the configured broker source."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source", default=None)
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=int, default=1800)

    def handle(self, *args: object, **options: object) -> None:
        source_name = options.get("source") or settings.ALERT_SOURCE
        if not isinstance(source_name, str):
            raise CommandError("The alert source name must be a string.")
        once = options.get("once", False) is True
        interval = options.get("interval", 1800)
        if not isinstance(interval, int):
            raise CommandError("The ingest interval must be an integer.")
        try:
            source = get_source(source_name)
        except ValueError as error:
            raise CommandError(str(error)) from error

        while True:
            started_at = datetime.now(timezone.utc)
            try:
                counts = ingest(source, source_cursor(source_name))
                mark_source_succeeded(source_name, started_at)
                self.stdout.write(
                    f"{source_name}: created={counts[0]} "
                    f"skipped={counts[1]} invalid={counts[2]}"
                )
            except (OSError, ValueError, KeyError, TypeError):
                logger.exception("Alert ingestion failed for %s", source_name)
                if once:
                    return
            if once:
                return
            time.sleep(interval)
