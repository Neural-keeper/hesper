# Hesper

Hesper is a full-stack Django application that helps amateur astronomers quickly answer a practical question: what is worth observing tonight from my location? The platform ingests astronomy alert data, filters it against local conditions, and surfaces the most relevant events in a clean, accessible interface.

## Overview

Modern astronomy alert feeds are rich with data but difficult for non-specialists to interpret. Hesper bridges that gap by turning raw event streams into a curated observing experience. It combines backend data processing, scientific calculations, and a user-focused interface to help users identify which alerts are visible, timely, and worth pursuing.

The project is designed to demonstrate end-to-end engineering in a realistic domain: data ingestion, backend modeling, scientific computation, and deployment in a production-like stack.

## Features

- User accounts with location-aware observing context
- Astronomy alert ingestion from external data sources
- Visibility and timing calculations based on observer location and sky conditions
- Curated "Tonight's Sky" recommendations
- Accessible, server-rendered interface using Django templates and HTMX
- Automated scheduled ingestion and operational workflows
- Production-ready deployment pattern with PostgreSQL and cloud hosting

## Tech stack

| Layer | Technology | Role |
|---|---|---|
| Backend | Python 3.12, Django 5.2 | Application structure, authentication, business logic, and data models |
| Database | PostgreSQL | Persistent storage for user data and alert-related records |
| Astronomy | Astropy, astroplan, timezonefinder | Sky and visibility calculations, local time handling, and event analysis |
| Frontend | Django templates, HTMX, custom CSS | Fast, accessible UI with lightweight interactivity |
| Local environment | Docker, Docker Compose | Consistent development setup and service orchestration |
| Testing | pytest, pytest-django | Automated validation of application behavior |
| Linting / typing | Ruff, mypy | Code quality, consistency, and static analysis |
| Deployment | Render, Gunicorn, WhiteNoise | HTTPS serving and production deployment |
| Tooling | uv | Fast dependency management and reproducible environment setup |
| Automation | GitHub Actions | Scheduled ingest workflows and operational automation |

## System architecture

The application follows a straightforward data flow:

1. External astronomy alert sources publish new events.
2. The ingestion layer retrieves and normalizes the data.
3. Domain logic evaluates whether each event is relevant for a given observer location and timeframe.
4. The system ranks and filters alerts into a user-facing recommendation list.
5. Users view the best opportunities in a clear, accessible interface.

This architecture keeps the data pipeline explicit and maintainable while making it easy to extend the system as the feature set grows.

## Repository structure

- `accounts/` — user and profile logic
- `alerts/` — alert ingestion and domain processing
- `config/` — Django settings and application configuration
- `core/` — shared utilities and common functionality
- `lore/` — astronomy and cultural lore data
- `observers/` — observer-specific logic and user context
- `sky/` — astronomy and visibility-related calculations
- `templates/` — UI templates for the web application
- `tonight/` — recommendation flow and user-facing event presentation
- `manage.py` — Django entry point

## Development setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- uv

### Install dependencies

```bash
uv sync
```

### Run locally

```bash
make up
```

This starts the local development stack with Docker Compose.

### Run migrations

```bash
make migrate
```

### Run tests and checks

```bash
make test
```

### Trigger ingestion once

```bash
make ingest
```

## Deployment

The project is structured for deployment on a lightweight cloud service with PostgreSQL and static asset serving. The current setup targets a simple production path using Render and standard Django deployment tooling, while preserving a local Docker environment for development.

## Why this project matters

Hesper demonstrates a practical, product-oriented engineering approach in a specialized domain. It combines:

- backend application development
- scientific data processing
- user experience design
- production deployment planning
- automation and maintenance workflows

This makes it a strong example of software engineering that spans technical implementation and real-world product usefulness.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
