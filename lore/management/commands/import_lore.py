from __future__ import annotations

import csv
import gzip
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lore.models import CulturalConstellation, SkyCulture, Star

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STELLARIUM_URL = (
    "https://github.com/Stellarium/stellarium/tree/"
    "3059843b82e22e31bd3e0f7cf13d0f292e72ef54/skycultures"
)
HYG_URL = "https://codeberg.org/astronexus/hyg"


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def _license(text: str) -> str:
    return _section(text, "License").strip()


def _credit(text: str) -> str:
    return _section(text, "Authors").strip()


def _constellation_descriptions(text: str) -> dict[str, str]:
    section_match = re.search(
        r"^## Constellations\s*$([\s\S]*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE,
    )
    if not section_match:
        return {}
    section = section_match.group(1)
    headings = list(re.finditer(r"^#{3,6}\s+(.+?)\s*$", section, re.MULTILINE))
    descriptions: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        description = section[start:end].strip()
        if description:
            descriptions[_normalized(heading.group(1))] = description
    return descriptions


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag == "td" and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def _greek_descriptions(text: str) -> dict[str, tuple[str, str]]:
    parser = _TableParser()
    parser.feed(text)
    descriptions: dict[str, tuple[str, str]] = {}
    for row in parser.rows:
        if len(row) < 6:
            continue
        abbreviation, native, translation, iau_name, hints, art = row[:6]
        if abbreviation == "Abbreviation":
            continue
        if not iau_name:
            continue
        description = "\n".join(
            part for part in (native, translation, iau_name, hints, art) if part
        )
        descriptions[abbreviation] = (iau_name, description)
    return descriptions


def _figure_hips(record: dict[str, Any]) -> list[int]:
    return sorted(
        {
            int(hip)
            for line in record.get("lines", [])
            for hip in line
            if isinstance(hip, int)
        }
    )


class Command(BaseCommand):
    help = "Import licensed sky-culture and bright-star data."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        try:
            star_count = self._import_stars()
            culture_count, constellation_count, skipped_count = self._import_cultures()
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise CommandError(f"Lore import failed: {error}") from error
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {star_count} bright stars, {culture_count} cultures, "
                f"{constellation_count} cultural constellations; skipped "
                f"{skipped_count} entries without descriptions."
            )
        )

    def _import_stars(self) -> int:
        path = DATA_DIR / "hyg" / "hyg_v44.csv.gz"
        imported = 0
        with gzip.open(path, "rt", newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if not row["hip"] or not row["ra"] or not row["dec"] or not row["mag"]:
                    continue
                magnitude = float(row["mag"])
                if magnitude >= 6:
                    continue
                Star.objects.update_or_create(
                    hip_number=int(row["hip"]),
                    defaults={
                        "proper_name": row["proper"] or None,
                        "ra_deg": float(row["ra"]) * 15,
                        "dec_deg": float(row["dec"]),
                        "magnitude": magnitude,
                    },
                )
                imported += 1
        return imported

    def _import_cultures(self) -> tuple[int, int, int]:
        configs = (
            ("modern", "Modern (IAU)", "World"),
            ("indian", "Indian Vedic", "Southern Asia"),
            ("greek_almagest", "Greek (Almagest)", "Northern Africa"),
            ("indian_nakshatras", "Indian (Nakshatras)", "India"),
        )
        skipped_count = 0
        for directory, name, region in configs:
            folder = DATA_DIR / "stellarium" / directory
            description = (folder / "description.md").read_text(encoding="utf-8")
            culture, _ = SkyCulture.objects.update_or_create(
                name=name,
                defaults={
                    "region_or_people": region,
                    "description": description,
                    "source_url": f"{STELLARIUM_URL}/{directory}",
                    "license": _license(description),
                    "credit_text": _credit(description),
                },
            )
            index = json.loads((folder / "index.json").read_text(encoding="utf-8"))
            if directory == "greek_almagest":
                greek_descriptions = _greek_descriptions(description)
                for record in index.get("constellations", []):
                    abbreviation = record["id"].rsplit(" ", 1)[-1]
                    parsed = greek_descriptions.get(abbreviation)
                    if parsed is None:
                        skipped_count += 1
                        continue
                    iau_name, text = parsed
                    self._upsert_constellation(
                        culture,
                        record,
                        record["common_name"],
                        text,
                        iau_name,
                        directory,
                    )
            else:
                descriptions = _constellation_descriptions(description)
                for record in index.get("constellations", []):
                    common_name = record.get("common_name", {})
                    candidates = (
                        common_name.get("english", ""),
                        common_name.get("pronounce", ""),
                        common_name.get("native", ""),
                    )
                    constellation_text = next(
                        (
                            descriptions[_normalized(candidate)]
                            for candidate in candidates
                            if _normalized(candidate) in descriptions
                        ),
                        None,
                    )
                    if not constellation_text:
                        skipped_count += 1
                        continue
                    self._upsert_constellation(
                        culture,
                        record,
                        common_name,
                        constellation_text,
                        None,
                        directory,
                    )
        imported_names = [name for _, name, _ in configs]
        return (
            SkyCulture.objects.filter(name__in=imported_names).count(),
            CulturalConstellation.objects.filter(
                culture__name__in=imported_names
            ).count(),
            skipped_count,
        )

    def _upsert_constellation(
        self,
        culture: SkyCulture,
        record: dict[str, Any],
        common_name: dict[str, str],
        description: str,
        iau_name: str | None,
        directory: str,
    ) -> None:
        native_name = common_name.get("native") or iau_name or record["id"]
        CulturalConstellation.objects.update_or_create(
            culture=culture,
            native_name=native_name,
            defaults={
                "english_name": common_name.get("english") or iau_name,
                "description": description,
                "stars": _figure_hips(record),
                "source_url": f"{STELLARIUM_URL}/{directory}/description.md",
                "license": _license(
                    (DATA_DIR / "stellarium" / directory / "description.md").read_text(
                        encoding="utf-8"
                    )
                ),
            },
        )
