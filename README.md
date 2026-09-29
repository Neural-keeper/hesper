# hesper Build Guide: Prompting an AI to Build the Django Foundation

This guide walks you through building a working first version of hesper with an AI coding assistant such as Claude Code, Cursor, or Copilot. It has three parts:

1. **A project context file.** Put it in the repository once, and every AI session starts with the same rules.
2. **Nine phase prompts.** Copy and paste them one at a time. Each one ends in something you can run and test.
3. **Review checklists and helper prompts.** Use these to verify the AI's work and to learn the code as you go.

The goal is a **foundation**: a simple, working, accessible system that is organized so the advanced features in the README (Kafka streaming, the filter language, push notifications) can be added later without a rewrite.

## Develop in Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg?repo=Neural-keeper/hesper)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=Neural-keeper/hesper)

The repository includes a development container with Python 3.12, uv, Docker-in-Docker, the Python/Ruff/Django VS Code extensions, and port 8000 forwarded as **hesper web**. The configuration requests the smallest Codespaces machine size: 2 cores. GitHub may offer different sizes depending on account and repository limits.

### Start and stop a Codespace

1. Select the badge above, choose the repository and branch, and create the Codespace.
2. Wait for the container setup to finish. It installs uv and runs `uv sync` automatically.
3. Start the development stack from the VS Code terminal with `make up`.
4. Open the forwarded **hesper web** port when Django is ready.
5. Stop the Codespace from the Codespaces menu in GitHub, or run `gh codespace stop` from a local GitHub CLI installation. Stopping it preserves the environment without consuming active compute time.

Check remaining free Codespaces hours at [GitHub billing and plans](https://github.com/settings/billing), under **metered usage** and **Codespaces**. Free quotas and account eligibility can change, so use the current billing page as the source of truth.

### Store broker credentials safely

Do not put broker credentials in `.env`, commit them, or add them to `devcontainer.json`. In GitHub, open **Settings > Codespaces > Secrets and variables > Codespaces**, create a secret using the exact environment variable name expected by the broker source, and select the repository access scope. Rebuild or restart the Codespace after adding a secret. Codespaces injects the value into the environment; the application reads it through Django settings. Keep only placeholder variable names in `.env.example`.

---

## Contents

- [Part 1: How to work with the AI](#part-1-how-to-work-with-the-ai)
- [Develop in Codespaces](#develop-in-codespaces)
- [Part 2: The foundation's design](#part-2-the-foundations-design)
- [Part 3: The project context file](#part-3-the-project-context-file)
- [Part 4: Phase prompts](#part-4-phase-prompts)
- [Part 5: Review checklist](#part-5-review-checklist)
- [Part 6: Helper prompts](#part-6-helper-prompts)
- [Part 7: From foundation to full system](#part-7-from-foundation-to-full-system)

---

## Part 1: How to work with the AI

**One phase per session.** Start a fresh conversation for each phase. Long sessions drift: the AI forgets earlier decisions and starts contradicting them. The context file (Part 3) carries the important rules between sessions.

**Plan first, then code.** Every phase prompt ends by asking the AI to propose a plan and wait. Read the plan before approving it. Catching a bad idea in a plan takes one minute; catching it in 400 lines of code takes an hour.

**Run it yourself.** After each phase, run the tests and click through the app yourself. Do not accept "all tests pass" from the AI without seeing it.

**Commit after every working phase.** If a later phase goes wrong, you can return to the last working version with `git reset` or `git checkout`.

**Understand every file.** You will be asked about this project in interviews. Use the "explain" prompt in Part 6 on anything you don't understand before moving on.

**Never let the AI invent facts.** Two areas matter most here:
- **Broker APIs.** The AI does not reliably know any broker's current endpoints or data format. You will read the broker's documentation yourself and paste the relevant parts into the prompt (Phase 7).
- **Cultural lore.** The AI will write convincing myths that do not exist. All lore comes from sourced data files that you download (Phase 6).

---

## Part 2: The foundation's design

### What the foundation does

A user signs up, enters their location and telescope's limiting magnitude, and sees **Tonight's Sky**: a list of recent alerts that will be above their horizon during tonight's darkness and bright enough to see. Each alert shows when it's best observed, its constellation, and the sky lore connected to that part of the sky.

### Stack

| Layer | Choice | Why it's right for a foundation |
|---|---|---|
| Language | Python 3.12 | Direct access to the astronomy libraries |
| Web framework | Django 5.2 (LTS) | Authentication, database models, admin panel, and forms are built in |
| Pages | Django templates + HTMX | Server-rendered HTML works without JavaScript and is easier to make accessible than a single-page app; HTMX adds partial page updates where helpful |
| Styling | Plain CSS with custom properties | Full control over contrast, focus styles, and the red night mode |
| Database | PostgreSQL: Docker locally, Neon's free tier in production | Production-grade from the start, at no cost |
| Background work | A Django management command: a loop in a container locally, and a scheduled GitHub Actions workflow in production | Free and needs no always-on server; replaced by Celery or Kafka later |
| Astronomy | Astropy, astroplan, timezonefinder | Coordinates, darkness times, altitude, constellations, local time zones |
| Dependencies | uv | Fast, with a lockfile |
| Testing | pytest + pytest-django | Standard and readable |
| Deployment | Render free web service (Gunicorn + WhiteNoise); Docker Compose locally | Free HTTPS and deploys on every Git push, no credit card |

### Running it for $0

Everything in the foundation runs on free tiers. Free tiers change often, so confirm current limits on each provider's pricing page before you rely on them.

| Need | Free option | Limits that shape the design |
|---|---|---|
| Web app | Render free web service | Spins down after 15 minutes without traffic, and the next visit takes about a minute to wake it. No free always-on background workers. |
| Database | Neon free plan | 0.5 GB of storage and 100 compute-hours per month per project. The database sleeps after 5 minutes idle, and it only uses compute hours while awake. |
| Scheduled ingestion | GitHub Actions scheduled workflow (free for public repositories) | Runs at most every 5 minutes, and runs can start late when GitHub is busy. Scheduled workflows are paused after 60 days with no repository activity. |
| HTTPS and address | Render's free `onrender.com` subdomain | A custom domain costs money, unless you use a free first-year domain from the GitHub Student Developer Pack. |
| Email for password resets | A transactional email service's free tier (for example Brevo or Resend), or leave resets off at first | Daily sending caps, which is plenty for a small user base. |
| Web Push (later) | Built into browsers; no paid service needed | None worth worrying about. |
| Broker data, Astropy, Stellarium data | Free | Follow each source's terms and license. |

**How the design fits these limits:**
- **Storage (0.5 GB).** Only alerts brighter than magnitude 20 are stored, since no observer's telescope can see fainter ones. Alerts older than 7 days are deleted every day. Cutout images are linked from the broker, never stored, and the raw payload is trimmed.
- **Database compute (100 hours).** Ingestion runs every 30 minutes rather than continuously. Each run wakes the database for a few minutes, about 36 compute-hours a month at the smallest size, which leaves room for web traffic. Faster polling would use up the allowance.
- **No free worker.** In production, GitHub Actions runs `manage.py run_ingest --once` on a schedule instead of a long-running worker process. Locally, the Docker worker still runs the loop.
- **Cold starts.** The first visit after a quiet period is slow. That's fine for a portfolio project. When hesper has regular users, move to the always-on option below.

**Always-on alternative, also free:** Oracle Cloud's Always Free tier includes an Arm virtual machine that can run the whole Docker Compose setup with no spin-down. In 2026 Oracle cut that allowance to 2 CPUs and 12 GB of memory, and it disabled some instances that exceeded the new limits. That is still plenty for hesper, but keep backups and treat it as a free tier that can change without warning. It also needs a credit card for identity verification. The GitHub Student Developer Pack's cloud credits are another route when you need an always-on server.

### Django apps

```
hesper/
├── config/          # Django settings, URLs, WSGI
├── core/            # base templates, CSS, accessibility helpers, home page
├── observers/       # user profile: location, limits, interests, display preferences
├── alerts/          # Alert model, alert sources, ingestion command
├── sky/             # astronomy calculations: darkness, visibility, constellations (no Django imports)
├── lore/            # sky cultures, star names, stories, sources
└── tonight/         # matching logic and the Tonight's Sky page
```

### Three design rules that make future upgrades easy

**1. Alert sources sit behind one interface.** Every source (sample data, a broker's REST API, and later Kafka) implements the same small interface:

```python
class AlertSource(Protocol):
    def fetch(self, since: datetime) -> Iterable[NormalizedAlert]: ...
```

The ingestion command doesn't know or care which source it's using. Switching to Kafka later means writing one new class.

**2. Logic lives in plain functions, not views.** Astronomy math, matching, and lore lookup are ordinary Python functions in `services.py` or `sky/` modules. Views only call them and render templates. This makes the logic easy to test, and it can be moved into separate services later.

**3. Matching is one function.** For now, matching loops over each alert for each user, which is fine for a small number of users. Because it is isolated in `tonight/services.py::match_alerts_for_observer`, it can later be replaced with the HEALPix index described in the README without touching anything else.

### Accessibility requirements

These apply to every page, in every phase. The target is **WCAG 2.2 level AA**.

- **Structure:** semantic HTML (`header`, `nav`, `main`, `footer`), one `h1` per page, headings in order, and a "Skip to main content" link.
- **Keyboard:** every feature works with the keyboard alone, in a logical tab order, with a clearly visible focus outline. Never remove the outline without replacing it.
- **Contrast:** at least 4.5:1 for normal text and 3:1 for large text and interface controls, in every theme.
- **Color is never the only signal.** For example, "visible now" gets a text label or icon, not just a green color.
- **Forms:** every input has a visible `<label>`. Errors are shown in text next to the field, summarized at the top of the form, and linked to the field with `aria-describedby`.
- **Images:** alert cutouts get useful alt text, such as "Difference image of alert 12345 in Orion, showing a new point source".
- **Updates:** content refreshed with HTMX is announced to screen readers through an `aria-live="polite"` region.
- **Motion:** respect `prefers-reduced-motion`.
- **Zoom:** layouts work at 200% zoom and on 320px-wide screens without horizontal scrolling.
- **Works without JavaScript:** core features function with JavaScript turned off. HTMX only enhances them.
- **Night mode:** a red-on-black theme for use at the telescope, since red light preserves night vision. It must still meet the contrast targets.

---

## Part 3: The project context file

Save the block below as **`CLAUDE.md`** in the repository root. Claude Code reads this file automatically at the start of every session. For other tools, name it `AGENTS.md` or paste it at the start of each session.

````markdown
# hesper: project context for AI assistants

## What this project is
hesper filters the Vera C. Rubin Observatory alert stream for amateur astronomers.
A user enters their location and telescope limits and sees "Tonight's Sky": recent
alerts that will be above their horizon during tonight's darkness and bright enough
to see, with the cultural sky lore connected to that part of the sky.

This is the FOUNDATION version: simple, working, and accessible, structured so that
Kafka streaming, a filter language, and push notifications can be added later.

## Stack
- Python 3.12, Django 5.2 LTS, PostgreSQL, uv for dependencies
- Django templates + HTMX (progressive enhancement only), plain CSS
- Astropy, astroplan, timezonefinder
- pytest + pytest-django
- Local: Docker Compose. Production: Render free web service (Gunicorn + WhiteNoise),
  Neon free Postgres, GitHub Actions scheduled workflow for ingestion

## Apps
config/, core/, observers/, alerts/, sky/, lore/, tonight/
- sky/ contains pure astronomy functions and must not import Django.
- Business logic lives in services.py modules or sky/, never in views.
- Views are thin: parse the request, call a service, render a template.

## Non-negotiable rules
1. Never invent external API endpoints, fields, or data formats. If you need
   information about a broker API, stop and ask me for the documentation.
2. Never write, generate, or paraphrase cultural lore or star-name meanings from
   your own knowledge. All lore comes from data files I provide, and every story
   stores and displays its source and license.
3. Every page meets WCAG 2.2 AA: semantic HTML, keyboard access with visible focus,
   4.5:1 text contrast in every theme, labels on all inputs, text error messages,
   alt text on images, aria-live for HTMX updates, reduced-motion support, and
   core features that work without JavaScript.
4. All datetimes are timezone-aware and stored in UTC (USE_TZ = True). Convert to
   the observer's local time zone only for display.
5. Secrets come from environment variables. Never commit secrets. Keep
   .env.example up to date.
6. Every new function with logic gets tests. Astronomy functions get tests with
   known, hand-checkable values.
7. Use type hints everywhere. Code must pass ruff and mypy.
8. Keep dependencies minimal. Ask before adding a new package.
9. Alert sources implement the AlertSource protocol in alerts/sources/base.py.
10. Everything must run on free tiers. Keep the database under 400 MB: store only
    alerts brighter than INGEST_MAX_MAGNITUDE (default 20), delete alerts older
    than ALERT_RETENTION_DAYS (default 7), never store images in the database, and
    trim raw payloads. Do not add services that require a paid plan or an always-on
    background process in production.

## Workflow
- Before writing code, propose a plan (files to create or change, models, tests)
  and wait for my approval.
- Make small, reviewable changes.
- After implementing, run: `uv run ruff check . && uv run mypy . && uv run pytest`
  and show me the output.
- Explain anything non-obvious in a short comment or in the pull request summary.
- If a requirement is ambiguous, ask instead of guessing.

## Commands
- `make up`: start everything with Docker Compose
- `make test`: lint, type check, run tests
- `make ingest`: fetch alerts once from the configured source
- `make seed`: load sample alerts and a demo observer
````

---

## Part 4: Phase prompts

Each prompt follows the same pattern: **goal, requirements, constraints, done-when checks, then "propose a plan and wait."** Copy each block into a new AI session. Edit anything in `[brackets]`.

### Phase 0: Scaffold the project

*Estimated time: 1–2 evenings*

```text
Read CLAUDE.md first. We are starting Phase 0: scaffolding.

Goal: an empty but fully working Django project with tooling, Docker, and CI.

Requirements:
- Django 5.2 project named "config" with apps: core, observers, alerts, sky, lore, tonight.
  sky/ is a plain Python package, not a Django app with models.
- uv for dependency management with a lockfile. Initial dependencies: django,
  psycopg[binary], django-environ, gunicorn, whitenoise, django-htmx.
  Dev dependencies: pytest, pytest-django, ruff, mypy, django-stubs.
- Settings read from environment variables via django-environ, with a checked-in
  .env.example. DEBUG defaults to False. USE_TZ = True, TIME_ZONE = "UTC".
- docker-compose.yml with services: db (PostgreSQL 16), web (Gunicorn), worker
  (placeholder command that sleeps for now).
- Makefile with targets: up, down, test, migrate, shell, ingest, seed.
- GitHub Actions workflow running ruff, mypy, and pytest on every push, using a
  PostgreSQL service container.
- core app: a base.html template with a skip link, header, nav, main, and footer,
  plus a home page that says "hesper" with a one-sentence description.
- core/static/css/main.css with color tokens as CSS custom properties, a visible
  focus style, and a prefers-reduced-motion rule.
- One smoke test confirming the home page returns 200 and contains an h1.

Constraints:
- No frontend build step. No JavaScript frameworks.
- Do not implement any features beyond the scaffold.

Done when:
- `make up` serves the home page at localhost:8000.
- `make test` passes locally and in GitHub Actions.
- The home page is fully usable with the keyboard, and the skip link works.

Propose a plan and wait for my approval before writing code.
```

### Phase 1: Data models and admin

*Estimated time: 1–2 evenings*

```text
Read CLAUDE.md first. We are starting Phase 1: data models.

Goal: the database models for observers and alerts, visible in the Django admin.

Models:

observers.ObserverProfile (one-to-one with the Django User)
- display_name
- latitude (decimal degrees, -90 to 90), longitude (-180 to 180), elevation_m (default 0)
- timezone (IANA name, derived from coordinates, stored for display)
- min_altitude_deg (default 30, range 0 to 80)
- limiting_magnitude (default 14.0, range 5 to 20)
- interests: which alert classes the user wants (supernova, variable star,
  nova, asteroid, other). Choose a sensible representation and explain why.
- theme preference: system, light, dark, night-red

alerts.Alert
- source (which alert source it came from) and source_alert_id (unique together)
- object_id (the broker's ID for the underlying object, if any)
- observed_at (UTC), received_at (UTC)
- ra_deg, dec_deg
- magnitude, magnitude_error (nullable), band (for example g, r, i)
- alert_class (nullable) and class_confidence (nullable, 0 to 1)
- cutout_url (nullable). Never store images in the database; the free database tier is small.
- raw: JSON field holding a trimmed copy of the original payload for debugging
  (no image data, no large arrays)
- Indexes on observed_at and on (source, source_alert_id)

Requirements:
- Model-level validation for all ranges.
- Admin pages for both models with useful list columns, filters, and search.
- A NormalizedAlert dataclass in alerts/types.py matching the Alert fields.
  Sources return this type; only the ingestion code turns it into database rows.
- Tests for validation rules and for the unique constraint.

Constraints:
- Do not add visibility, matching, or lore fields yet.

Done when:
- Migrations run cleanly on an empty database.
- I can create an observer and an alert in the admin.
- All tests pass.

Propose a plan and wait for my approval before writing code.
```

### Phase 2: Astronomy helpers

*Estimated time: 2–3 evenings. This is the most important phase to get right.*

```text
Read CLAUDE.md first. We are starting Phase 2: the sky/ package.

Goal: pure, well-tested astronomy functions using astropy and astroplan.
sky/ must not import Django.

Functions:

1. dark_window(lat, lon, elevation_m, now) -> NightWindow
   Returns the start and end of astronomical darkness (Sun below -18 degrees) for
   "tonight": if it's currently dark, the current night; otherwise the next night.
   If astronomical darkness never occurs (high latitudes in summer), fall back to
   nautical darkness (-12 degrees), then civil (-6), and record which one was used.
   If the Sun never sets, return a clear "no darkness" result instead of raising.

2. visibility(ra, dec, observer_location, window, min_altitude_deg) -> Visibility
   Samples the dark window (for example every 10 minutes) and returns:
   - is_observable (bool): altitude exceeds min_altitude_deg at some point in the window
   - best_time (UTC) and max_altitude_deg
   - observable_from and observable_until (UTC, nullable)
   - moon_separation_deg at best_time, moon_illumination (0 to 1)

3. constellation_of(ra, dec) -> ConstellationInfo
   Uses astropy's get_constellation to return the IAU abbreviation and full name.

4. flux_to_ab_mag(flux_njy) -> float
   mag = -2.5 * log10(flux_njy) + 31.4. Raise a clear error for zero or negative flux.

5. timezone_for(lat, lon) -> str using timezonefinder.

Tests (use fixed dates so results never change):
- Maximum altitude check: for an object at declination dec seen from latitude lat,
  the highest possible altitude is 90 - |lat - dec|. Test several cases, including
  an object at dec -70 seen from lat +28, which must never be observable.
- An object at dec +89 seen from lat +28 stays near altitude 28 all night.
- Tampa, Florida (27.95 N, 82.46 W) on a fixed winter date has a normal dark window.
- A location at 70 N in late June uses a fallback darkness level or returns
  "no darkness", and does not raise.
- flux_to_ab_mag(3631e9) is 0 within a small tolerance.
- constellation_of returns Orion for RA 83.8, Dec -5.4.
- Timezone for Tampa is America/New_York.

Constraints:
- Use frozen dataclasses for return types.
- Keep sampling resolution a parameter with a sensible default.
- Add a short docstring to each function explaining the astronomy in plain language.

Done when:
- All tests pass, and I have hand-checked the maximum-altitude cases on paper.

Propose a plan and wait for my approval before writing code.
```

### Phase 3: Sample alert source and ingestion

*Estimated time: 1–2 evenings*

```text
Read CLAUDE.md first. We are starting Phase 3: alert sources and ingestion.

Goal: a working ingestion pipeline using realistic sample data, so the whole app
works before connecting to a real broker.

Requirements:
- alerts/sources/base.py: an AlertSource protocol with
  fetch(since: datetime) -> Iterable[NormalizedAlert] and a name property.
- alerts/sources/sample.py: SampleSource, which generates realistic synthetic alerts:
  - Random positions across the southern and equatorial sky (dec -90 to +30)
  - Magnitudes weighted toward faint values (most fainter than 18) with a small
    fraction between 11 and 16, so there is always something bright
  - A mix of alert classes with confidence values
  - observed_at timestamps within the last 24 hours
  - A seed parameter so output is reproducible in tests
  - A clear marker in the raw payload saying the alert is synthetic
- alerts/services.py: ingest(source, since) that
  - saves new alerts and skips duplicates using (source, source_alert_id)
  - logs a warning and continues if one alert is invalid
  - returns counts of created, skipped, and invalid alerts
  - skips alerts fainter than settings.INGEST_MAX_MAGNITUDE (default 20)
- Management command `prune_alerts` that deletes alerts older than
  settings.ALERT_RETENTION_DAYS (default 7) and reports how many it removed.
- Management command `run_ingest` with options --source, --once, and
  --interval SECONDS. In loop mode it keeps running, logs each cycle, and keeps
  going if a cycle fails.
- Update the worker service in docker-compose.yml to run run_ingest in loop mode.
- Management command `seed` that creates a demo observer in Tampa and ingests one
  batch of sample alerts.
- The UI must label synthetic alerts as sample data wherever they appear.

Tests:
- Running ingest twice creates no duplicates.
- One invalid alert in a batch does not stop the rest.
- SampleSource with the same seed returns the same alerts.
- prune_alerts removes old alerts and keeps recent ones.
- Alerts fainter than INGEST_MAX_MAGNITUDE are not stored.

Done when:
- `make seed` then `make ingest` fills the database, visible in the admin.
- The worker container runs continuously and survives a simulated error.

Propose a plan and wait for my approval before writing code.
```

### Phase 4: Tonight's Sky

*Estimated time: 3–4 evenings*

```text
Read CLAUDE.md first. We are starting Phase 4: matching and the Tonight's Sky page.

Goal: a signed-in observer sees the alerts they can observe tonight.

Matching (tonight/services.py):
- match_alerts_for_observer(profile, now) -> list[MatchedAlert]
  1. Compute tonight's dark window for the observer.
  2. Consider alerts observed in the last [48] hours.
  3. Keep alerts brighter than the observer's limiting magnitude and in their interests.
  4. Compute visibility for each; keep only observable ones.
  5. Sort by best_time.
  Each MatchedAlert includes the alert, its visibility, and its constellation.
- Keep this function self-contained. It will be replaced by an indexed matcher
  later, so nothing else should depend on how it works internally.
- Cache the result per observer for [10] minutes using Django's cache framework.

Page (/tonight/):
- Header summary: the dark window in the observer's local time, the darkness level
  used, moon illumination, and the number of matches.
- Each alert as an article element with a heading, containing:
  - alert class and confidence in words (for example "Supernova, 82% confidence")
  - magnitude and band
  - constellation
  - best time (local), maximum altitude, observable-from and -until times
  - moon separation
  - cutout image with descriptive alt text, if available
  - a "Sample data" label for synthetic alerts
- Filter controls (class, maximum magnitude) as a normal GET form that works without
  JavaScript, enhanced with HTMX to update the list without a full page reload.
  The updated region is announced through an aria-live="polite" region.
- A helpful empty state that explains why there are no matches (for example "No
  darkness tonight at your latitude" or "Nothing brighter than magnitude 14 tonight")
  and suggests what to change.
- Times shown in the observer's time zone, with a time element carrying the UTC value.

Accessibility:
- Follow every rule in CLAUDE.md.
- Visibility status must be shown in text, not only color.

Tests:
- Matching with fixed alerts and a fixed "now" returns the expected set in order.
- An alert too far south for the observer is excluded.
- An alert fainter than the limit is excluded.
- The page requires login and renders for a user with no matches.

Done when:
- After `make seed`, the demo user sees a sensible list.
- The page works with keyboard only, with JavaScript disabled, and at 200% zoom.

Propose a plan and wait for my approval before writing code.
```

### Phase 5: Accounts, onboarding, and themes

*Estimated time: 2–3 evenings*

```text
Read CLAUDE.md first. We are starting Phase 5: accounts and observer setup.

Goal: a new visitor can sign up, set up their observing profile, and choose a theme.

Requirements:
- Sign up, log in, log out, and password reset using Django's built-in auth views,
  with accessible templates. Email can print to the console in development.
- After sign-up, redirect to an onboarding form for the ObserverProfile.
- Location entry:
  - Latitude and longitude number inputs, with an example and plain-language help text.
  - An optional "Use my current location" button that uses the browser's
    geolocation API to fill the fields. It must be clearly optional and explain
    what it does, and the form must work fully without it.
  - Show the resulting time zone after saving.
  - Do not add a geocoding service. City search can come later.
- Limiting magnitude input with help text giving typical values: naked eye about 6,
  binoculars about 9, small telescope 11 to 13, telescope with a camera 15 or more.
- A settings page to edit the profile later.
- Themes: system (follows prefers-color-scheme), light, dark, and night-red.
  - Implemented with CSS custom properties on a data-theme attribute.
  - The choice is saved on the profile and applied server-side so there is no flash.
  - Night-red uses only red tones on black and still meets 4.5:1 text contrast.
    Show me the measured contrast ratios for each theme's main text and links.
- Form errors: summary at the top linking to each field, plus inline messages
  connected with aria-describedby, with focus moved to the summary on failure.

Tests:
- Sign-up leads to onboarding, and onboarding leads to /tonight/.
- Invalid coordinates show accessible errors.
- The theme choice appears in the rendered HTML.

Done when:
- A new user can go from sign-up to Tonight's Sky using only the keyboard.

Propose a plan and wait for my approval before writing code.
```

### Phase 6: Cultural sky lore

*Estimated time: 3–5 evenings, mostly spent choosing and reviewing data*

**Before this phase, you do the research.** Download the sky culture data from Stellarium's GitHub repositories (look for the sky cultures directory). Choose 3–4 cultures, and for each one confirm its license and the credits the data requires. Also download a bright-star catalog with Hipparcos (HIP) numbers and positions, such as the HYG database, and confirm its license. Put everything in `lore/data/` with a `SOURCES.md` file listing each source, URL, license, and date downloaded.

```text
Read CLAUDE.md first. We are starting Phase 6: cultural sky lore.

Goal: each alert shows sourced cultural lore for the part of the sky it appears in.

Data I have placed in lore/data/:
- [List the sky culture folders you downloaded]
- [Name of the star catalog file]
- SOURCES.md with sources and licenses

First, inspect the files and describe their structure to me before planning.
Do not assume a format.

Models:
- SkyCulture: name, region or people, description (from data), source_url,
  license, credit_text
- Star: hip_number, proper_name (nullable), ra_deg, dec_deg, magnitude
  (only stars brighter than magnitude 6)
- CulturalConstellation: culture, native_name, english_name (nullable),
  description (from data, nullable), stars (the HIP numbers in its figure),
  source_url, license

Import:
- A management command `import_lore` that loads the files, validates them, and
  reports counts. Running it twice must not duplicate data.
- Skip entries with no description instead of filling gaps.

Lookup (lore/services.py):
- lore_for_position(ra, dec) -> LoreResult
  1. The IAU constellation (from sky.constellation_of).
  2. The nearest named bright star within [10] degrees.
  3. Cultural constellations whose figures include a star within [10] degrees of the
     position, grouped by culture.

Display on each alert in Tonight's Sky:
- A "Sky lore" section using a details/summary element (collapsed by default,
  keyboard accessible): "Appeared in Orion, near Betelgeuse", then each culture's
  constellation name and description.
- Every item shows its culture and a source link, and the page footer lists all
  required credits.

Constraints (critical):
- Never generate, summarize, translate, or fill in lore text yourself. Display
  only text from the data files, exactly as provided.
- If a culture's license doesn't allow the use we need, stop and tell me.

Tests:
- Import is idempotent.
- lore_for_position for a point near Betelgeuse returns Orion and Betelgeuse.
- A point far from any bright named star returns only the IAU constellation.

Done when:
- Alerts show lore with visible sources, and every credit required by the licenses
  appears on the site.

Propose a plan and wait for my approval before writing code.
```

### Phase 7: Connect a real broker

*Estimated time: 2–4 evenings, depending on the broker*

**Before this phase, you do the research.** Choose one of Rubin's official community brokers (ALeRCE, AMPEL, ANTARES, Babamul, Fink, Lasair, or Pitt-Google). Prefer one with a documented REST API or Python client that serves Rubin alerts without a long approval process. Read its documentation and terms of use, create an account if needed, and make one request by hand (with `curl` or its Python client) so you know it works. Save one real response to `alerts/fixtures/[broker]_sample.json`.

While you're there, **check the brightness overlap described in the README's Known Challenges section**: how many alerts brighter than magnitude 16 appear in a typical night? The answer decides whether you need a second data source later.

```text
Read CLAUDE.md first. We are starting Phase 7: a real broker source.

Goal: a BrokerSource that fetches real Rubin alerts from [broker name].

Here is the relevant documentation, copied from the broker's site:
[Paste the endpoint documentation, authentication instructions, rate limits,
and field descriptions.]

A real sample response is saved at alerts/fixtures/[broker]_sample.json.

Requirements:
- alerts/sources/[broker].py implementing AlertSource.
- Use only endpoints and fields shown in the documentation above. If something we
  need is missing, stop and ask me rather than guessing.
- Map the broker's fields to NormalizedAlert. Document every mapping decision in a
  comment, especially how magnitude is derived. If the broker gives flux, use
  sky.flux_to_ab_mag. If it gives difference flux rather than total brightness,
  point that out to me before continuing.
- Credentials from environment variables, added to .env.example.
- Respect the documented rate limits, with timeouts and retries with backoff.
  Never retry forever.
- Keep the raw payload in Alert.raw.
- Record when each fetch last succeeded so the next fetch continues from there.
- Selecting the source is a setting (ALERT_SOURCE=sample or [broker]).

Tests:
- Parsing the saved fixture produces correct NormalizedAlerts. No network access
  in tests; mock HTTP calls.
- A timeout or error response is logged and does not crash the loop.

Done when:
- With ALERT_SOURCE=[broker], the worker fills the database with real alerts, and
  Tonight's Sky shows them without the "Sample data" label.

Propose a plan and wait for my approval before writing code.
```

### Phase 8: Deploy for free

*Estimated time: 2–3 evenings*

**Before this phase:** create free accounts on Render and Neon, create a Neon project, and copy its connection string. Make the GitHub repository public so scheduled workflows are free.

```text
Read CLAUDE.md first. We are starting Phase 8: free production deployment.

Goal: hesper running publicly over HTTPS on free tiers:
- Web: Render free web service
- Database: Neon free Postgres
- Ingestion: a GitHub Actions scheduled workflow

Requirements:
- render.yaml (Render Blueprint) defining one free web service that builds with uv,
  runs migrations and collectstatic on deploy, and starts Gunicorn. Explain how
  Render's build and start commands work before writing it.
- Static files served by WhiteNoise with compressed, cached files.
- DATABASE_URL from environment, using Neon's pooled connection string with SSL
  required. Set CONN_MAX_AGE and connection health checks appropriately for a
  database that sleeps when idle, and explain your choice.
- .github/workflows/ingest.yml:
  - runs on a schedule every 30 minutes, plus manual runs (workflow_dispatch)
  - installs dependencies with uv and caching
  - runs `manage.py run_ingest --once` against the production database
  - runs `manage.py prune_alerts` once a day
  - reads DATABASE_URL and broker credentials from GitHub Actions secrets
  - fails loudly with a clear log if ingestion fails
- Production settings: DEBUG off, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS from
  environment, secure cookies, HSTS, SECURE_PROXY_SSL_HEADER for Render's proxy.
  `manage.py check --deploy` must pass.
- A health check endpoint (/healthz) that returns 200 without touching the database,
  plus /healthz/db that checks the database connection.
- An admin-only status page showing the last successful ingestion time, the number
  of stored alerts, and the approximate database size, so I can watch the free limits.
- A backup workflow: a GitHub Actions job that runs weekly, dumps the database with
  pg_dump, and stores it as a workflow artifact. Document the restore procedure.
- docs/DEPLOY.md: step-by-step setup for Render, Neon, and GitHub secrets; how to
  deploy updates; how to restore a backup; and a "free tier limits" section listing
  each limit and how to check current usage.

Constraints:
- Only free plans. If any step would require a paid plan or a credit card, stop and
  tell me.
- No secrets in the repository.

Done when:
- The site loads over HTTPS at its onrender.com address and `check --deploy` passes.
- The scheduled workflow has run successfully at least three times in a row.
- I have restored a backup into a separate Neon branch or a local database.

Propose a plan and wait for my approval before writing code.
```

### Phase 9: Accessibility audit and polish

*Estimated time: 2–3 evenings*

```text
Read CLAUDE.md first. We are starting Phase 9: an accessibility audit.

Goal: verify and fix accessibility across the whole site, and add automated
checks so it stays accessible.

Requirements:
- Add automated accessibility tests with Playwright and axe-core that load every
  page (home, sign-up, log-in, onboarding, settings, Tonight's Sky with results,
  Tonight's Sky empty) in each theme, and fail on any serious or critical issue.
  Run these in CI.
- Produce a manual checklist in docs/ACCESSIBILITY.md covering what automated tools
  cannot check: keyboard-only use, screen reader flow (VoiceOver or NVDA),
  200% zoom, 320px width, JavaScript disabled, and reduced motion.
- Fix every issue found, and list what you fixed.
- Add an accessibility statement page describing the target (WCAG 2.2 AA), known
  limitations, and how to report a problem.

Done when:
- Automated checks pass in CI in every theme.
- I have completed the manual checklist myself with a screen reader.

Propose a plan and wait for my approval before writing code.
```

After Phase 9, ask the AI to update `README.md` so its stack and status match the Django foundation. The current README describes FastAPI and React, which now belong to the future roadmap.

---

## Part 5: Review checklist

Run through this after every phase, before committing.

**It works**
- [ ] `make test` passes, and I watched it run
- [ ] I used the new feature myself in the browser
- [ ] I tried at least one wrong input or failure case

**It's correct**
- [ ] I can explain what every new file does
- [ ] Astronomy results match a hand check or a trusted source like Stellarium
- [ ] No invented API fields, endpoints, or lore anywhere
- [ ] Times display correctly in my local time zone

**It's safe**
- [ ] No secrets in the diff (`git diff --staged` before committing)
- [ ] New settings are in `.env.example`
- [ ] No new dependency I didn't approve

**It's accessible**
- [ ] Keyboard only: I can reach and use everything, and I can always see where focus is
- [ ] Works with JavaScript disabled
- [ ] Readable at 200% zoom and in every theme

**It fits the design**
- [ ] Logic is in services or `sky/`, not in views
- [ ] `sky/` still has no Django imports
- [ ] New alert sources use the `AlertSource` interface

---

## Part 6: Helper prompts

**Understand code you didn't write**

```text
Explain [file or function] to me as if I'm going to be asked about it in a
technical interview. Cover what it does, why it's designed this way, what the
alternatives were, and what would break first if we had 100x more users or alerts.
Then ask me three questions to check my understanding.
```

**Debug a problem**

```text
Something is wrong. Here's what I expected, what actually happened, and the full
error output:
[Expected] [Actual] [Paste the full traceback or logs]

Don't change any code yet. First, list the most likely causes in order, and tell
me what to check or run to confirm each one.
```

**Review before committing**

```text
Review the current uncommitted changes as a strict senior engineer. Check them
against CLAUDE.md, including the accessibility rules. List problems by severity,
with file and line. Don't fix anything yet.
```

**Keep a session on track**

```text
Stop. Summarize what we've changed in this session, what's left for this phase,
and any decisions we made that should be added to CLAUDE.md.
```

**Write the resume bullet**

```text
Based on what this phase actually built and the numbers in [test output / logs],
suggest two resume bullets in the format: strong verb, what I built, measurable
result. Only use numbers we have actually measured.
```

---

## Part 7: From foundation to full system

The foundation is designed so each advanced feature in the README replaces one piece:

| README feature | What changes | What stays the same |
|---|---|---|
| Kafka streaming | Add a `KafkaSource` implementing `AlertSource`; the worker becomes a Kafka consumer | Models, matching, pages |
| HEALPix sky index | Replace the inside of `match_alerts_for_observer` | Its inputs and outputs, and the Tonight's Sky page |
| Filter language | Add a `dsl/` module; profile stores a filter string | Matching calls it as one more check |
| Push notifications | Add a notifier that runs after ingestion | Everything else |
| Ranking model | Add a score to `MatchedAlert` and sort by it | The page template, apart from one new field |
| Separate services | Move `sky/` and service functions into their own processes | The logic itself, which is already Django-free or isolated |
| Always-on worker and real-time push | Move from Render and GitHub Actions to one always-on server (Oracle Always Free or Student Pack credits) running the Docker Compose setup | The code; only the deployment changes |

**A good time to start these:** after hesper is deployed and a few real people have used it. Their feedback will tell you which upgrade matters most.