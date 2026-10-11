# Free deployment

This deployment uses only the free tiers of Render, Neon, and GitHub Actions.
Free-tier limits and pricing change, so check the provider dashboards before
accepting an upgrade or entering billing details.

## 1. Create Neon

1. Create a Neon project on the Free plan.
2. Choose a region close to the Render region.
3. Open **Connect**, select the production branch and database, and choose
   **Pooled connection**.
4. Copy the connection string without committing it anywhere. It must include
   `sslmode=require`.
5. Keep a direct connection string available for administrative `pg_dump` and
   restore work, but use the pooled URL for the web service and workflows.

The connection string is used only as the `DATABASE_URL` secret in Render and
GitHub Actions.

## 2. Create Render

Create a Web Service from the repository and select the Free plan. The
[`render.yaml`](../render.yaml) Blueprint contains the service configuration:

- `buildCommand` installs `uv`, installs the locked production dependencies,
  collects static files, and runs migrations once during deployment.
- `startCommand` runs Gunicorn and binds to Render's `$PORT`.
- `healthCheckPath` uses `/healthz`, which does not touch the database.

Set these Render environment variables:

| Variable | Value |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | A Render-generated secret or another long random value |
| `DATABASE_URL` | The Neon pooled URL, including `sslmode=require` |
| `ALLOWED_HOSTS` | The exact `*.onrender.com` hostname |
| `CSRF_TRUSTED_ORIGINS` | `https://<your-service>.onrender.com` |
| `ALERT_SOURCE` | `alerce` |
| `ALERT_RETENTION_DAYS` | `7` |
| `INGEST_MAX_MAGNITUDE` | `20` |
| `DATABASE_SSL_REQUIRE` | `true` |
| `CONN_MAX_AGE` | `60` |
| `CONN_HEALTH_CHECKS` | `true` |
| `SECURE_HSTS_SECONDS` | `3600` |

`CONN_MAX_AGE=60` avoids reconnecting for every request while limiting the
chance of retaining a connection after Neon suspends an idle compute. Django's
connection health checks validate a reused connection before handing it to a
request. Neon SSL is required by both the URL and `DATABASE_SSL_REQUIRE`.

Do not add a Render worker: ingestion runs in GitHub Actions on the free plan.

## 3. Configure GitHub Actions

Make the repository public only if that is your chosen way to avoid private
repository Actions limits. Public repository workflows still need the secret.
In **Settings > Secrets and variables > Actions**, add:

| Secret | Value |
| --- | --- |
| `DATABASE_URL` | The Neon pooled URL |
| `NEON_DIRECT_DATABASE_URL` | The Neon direct URL, used only by backups |

ALeRCE's public LSST endpoints do not require a credential. If the selected
broker later requires one, add its credential as a separate Actions secret and
map it in the workflow; never put it in YAML or source.

[`ingest.yml`](../.github/workflows/ingest.yml) runs ingestion every 30 minutes
and supports manual runs. It also runs `prune_alerts` daily. A non-zero command
exit fails the job. [`backup.yml`](../.github/workflows/backup.yml) creates a
weekly custom-format PostgreSQL dump and retains the artifact for seven days.

## 4. Deploy and verify

After Render deploys, verify:

```text
https://<your-service>.onrender.com/healthz
https://<your-service>.onrender.com/healthz/db
```

The first request can be slow while the free service wakes. From a local
checkout with deployment environment variables supplied out-of-band, run:

```bash
uv run python manage.py check --deploy
uv run python manage.py collectstatic --no-input
```

Do not put production values in `.env`, `.env.example`, the repository, or
shell history. The application admin can view the status page at
`/admin/status/` after signing in with a staff account.

## 5. Restore a backup

Download the dump artifact from a successful **Database backup** workflow.
Restore it either to a local PostgreSQL database or to a separate Neon branch,
not directly over production:

```bash
createdb hesper_restore
pg_restore --clean --if-exists --dbname="$RESTORE_DATABASE_URL" hesper-*.dump
```

For a Neon branch, create the branch first, copy its direct connection string
from Neon, set it only in the local `RESTORE_DATABASE_URL` environment, and
run the same `pg_restore` command. Inspect the restored data before deciding
whether any production recovery is necessary.

## Free-tier limits and monitoring

These limits are provider-controlled and may change:

- **Render Free Web Service:** one free web service, limited instance
  resources, sleep after inactivity, and a monthly free runtime allowance.
  Check the service's Usage/Billing page and deployment logs.
- **Neon Free:** project compute-hours, storage, data transfer, branch, and
  active-compute limits. Check the project's **Usage** page and branch
  dashboard. The admin status page reports approximate PostgreSQL database size.
- **GitHub Actions:** included minutes/storage depend on repository visibility,
  account, and artifact retention. Check **Actions > Usage** and delete old
  artifacts when appropriate.

The app's `/admin/status/` page reports the alert count, last successful
ingestion, source, and approximate database size. The weekly backup artifact
is intentionally retained for seven days to avoid silently consuming storage.
