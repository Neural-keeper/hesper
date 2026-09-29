.PHONY: up down test migrate shell ingest seed

up:
	docker compose up --build

down:
	docker compose down

test:
	uv run ruff check .
	uv run mypy .
	uv run pytest

migrate:
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

ingest:
	uv run python manage.py run_ingest --once

seed:
	uv run python manage.py seed
