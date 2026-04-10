# Operations Guide

This document explains how to run the stack, access each service, and operate the application locally.

## Running services

Current local Docker Compose services:

- `web`: Django application container
- `postgres`: PostgreSQL database
- `pgadmin`: database UI
- `opensearch`: search engine

Current local container names:

- `nbs_readapt_web`
- `nbs_readapt_postgres`
- `nbs_readapt_pgadmin`
- `nbs_readapt_opensearch`

Current runtime status can be checked with:

```bash
docker compose ps
```

## Port policy

All host-facing local ports stay in the `9500-9599` range.

Current assignments:

- `9500`: Django app
- `9501`: PostgreSQL
- `9502`: pgAdmin
- `9503`: OpenSearch API
- `9504`: OpenSearch metrics

## Start and stop

Start the stack:

```bash
docker compose up --build -d
```

Or use the helper script:

```bash
bash scripts/rebuild.sh
```

Stop the stack:

```bash
docker compose down
```

Stop the stack and remove named volumes:

```bash
docker compose down -v
```

## Helper scripts

Available helper scripts:

- [scripts/up.sh](/home/pranav/PyCharm/Parveen/nbs_readapt/scripts/up.sh)
- [scripts/rebuild.sh](/home/pranav/PyCharm/Parveen/nbs_readapt/scripts/rebuild.sh)
- [scripts/refresh_repository_data.sh](/home/pranav/PyCharm/Parveen/nbs_readapt/scripts/refresh_repository_data.sh)

What each script does:

`scripts/up.sh`

- runs `docker compose up -d`
- shows `docker compose ps`
- use this for normal code changes when you do not need an image rebuild

`scripts/rebuild.sh`

- runs `docker compose up --build -d`
- shows `docker compose ps`
- use this when you changed:
  - `Dockerfile`
  - `requirements/*`
  - system packages
  - container-level configuration
  - anything else that affects the built image

`scripts/refresh_repository_data.sh`

- runs migrations
- validates source files
- reimports the initial Excel bundle into PostgreSQL
- rebuilds the OpenSearch BM25 index
- writes a QA report to `data/exports/repository_qa_report.json`
- use this when you changed:
  - repository import logic
  - normalization logic
  - taxonomy cleanup logic
  - search document shaping
  - indexing logic

Recommended usage:

```bash
bash scripts/up.sh
bash scripts/rebuild.sh
bash scripts/refresh_repository_data.sh
```

If you want to make them directly executable:

```bash
chmod +x scripts/*.sh
./scripts/up.sh
./scripts/rebuild.sh
./scripts/refresh_repository_data.sh
```

## Website and backend access

Frontend application:

- URL: `http://localhost:9500/`
- Purpose: reference-style default frontend

Live Django application UI:

- URL: `http://localhost:9500/live/`
- Purpose: backend-driven search, browse, map, analytics, shortlist, record detail modal

Django admin:

- URL: `http://localhost:9500/admin/`
- Purpose: admin access, import batches, source imports, taxonomy inspection

Health endpoint:

- URL: `http://localhost:9500/health/`
- Purpose: quick app health check

Repository endpoints:

- `http://localhost:9500/repository/`
- `http://localhost:9500/repository/overview/`
- `http://localhost:9500/repository/qa/`
- `http://localhost:9500/repository/records/<pk>/`

Search endpoints:

- `http://localhost:9500/search/`
- `http://localhost:9500/search/query/`
- `http://localhost:9500/search/facets/`

## Database access

PostgreSQL host access:

- Host: `localhost`
- Port: `9501`
- Database name: value of `POSTGRES_DB` in `.env`
- User: value of `POSTGRES_USER` in `.env`
- Password: value of `POSTGRES_PASSWORD` in `.env`

Typical local connection:

```bash
psql -h 127.0.0.1 -p 9501 -U nbs_readapt -d nbs_readapt
```

pgAdmin access:

- URL: `http://localhost:9502/`
- Email: value of `PGADMIN_DEFAULT_EMAIL` in `.env`
- Password: value of `PGADMIN_DEFAULT_PASSWORD` in `.env`

Suggested pgAdmin server registration:

- Host: `postgres`
- Port: `5432`
- Maintenance DB: `POSTGRES_DB`
- Username: `POSTGRES_USER`
- Password: `POSTGRES_PASSWORD`

Important usage rule:

- use pgAdmin for inspection, QA, and occasional manual correction
- do not use pgAdmin as the normal bulk-ingestion path
- normal repository intake should come through the Excel import pipeline

## OpenSearch access

OpenSearch API:

- URL: `http://localhost:9503/`

OpenSearch metrics:

- URL: `http://localhost:9504/`

Important note:

- this project runs OpenSearch `3.5.0`
- `OPENSEARCH_INITIAL_ADMIN_PASSWORD` must be present in `.env`
- the container currently runs with `plugins.security.disabled=true` for local development

Quick checks:

```bash
curl -sS http://127.0.0.1:9503/
curl -sS http://127.0.0.1:9503/_cat/indices?v
```

## Rebuild policy

Use the normal startup path for code-only changes:

```bash
bash scripts/up.sh
```

Use a rebuild when you changed the image inputs:

- `Dockerfile`
- Python dependencies
- system packages
- image entrypoints

```bash
bash scripts/rebuild.sh
```

Use a data refresh when you changed import or indexing logic:

```bash
bash scripts/refresh_repository_data.sh
```

## Data change policy

Preferred path for new data:

1. validate Excel source files
2. import into PostgreSQL
3. rebuild the OpenSearch index

Typical commands:

```bash
docker compose exec web python manage.py validate_repository_sources
docker compose exec web python manage.py import_repository_sources
docker compose exec web python manage.py index_repository_records --recreate
```

Direct PostgreSQL edits are possible, including through pgAdmin, but they are an exception workflow.

If searchable repository data changes in PostgreSQL, reindex OpenSearch afterwards:

```bash
docker compose exec web python manage.py index_repository_records --recreate
```

## Environment file

Main environment file:

- [.env.sample](/home/pranav/PyCharm/Parveen/nbs_readapt/.env.sample)

Important variables:

- `APP_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PUBLIC_PORT`
- `PGADMIN_DEFAULT_EMAIL`
- `PGADMIN_DEFAULT_PASSWORD`
- `OPENSEARCH_URL`
- `OPENSEARCH_PUBLIC_PORT`
- `OPENSEARCH_INITIAL_ADMIN_PASSWORD`

## Core operational commands

Most day-to-day work can be done through the helper scripts above. The raw commands below are still useful when you need more control.

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Create a Django superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Run Django checks:

```bash
docker compose exec web python manage.py check
```

Tail logs:

```bash
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f opensearch
```

Open a Django shell:

```bash
docker compose exec web python manage.py shell
```

## Application usage

Primary user-facing UI tabs:

- `Search & Browse`
- `Map`
- `Analytics`

Key repository workflows already available:

- search records by keyword
- filter by source dataset, country, geography type, hazard, NbS type, implementation stage, policy level, and year
- view record details in modal
- build a local shortlist
- inspect repository aggregates and mapped records

For production deployment, use [DEPLOY_TRAEFIK.md](/home/pranav/PyCharm/Parveen/nbs_readapt/DEPLOY_TRAEFIK.md).

## Admin workflows

Import batches:

- URL: `http://localhost:9500/admin/repository/importbatch/`

From there you can:

- open `Import Sources`
- validate registered source files before import
- import from a server-side directory
- upload registered Excel files directly
- create an `ImportBatch` record with notes

## Troubleshooting

If the app is up but search returns nothing:

- check PostgreSQL import state
- check the OpenSearch index exists
- rerun indexing from PostgreSQL

Useful commands:

```bash
docker compose exec web python manage.py import_initial_input --reset
docker compose exec web python manage.py index_repository_records --recreate
docker compose exec web python manage.py report_repository_qa
```

If OpenSearch fails to start:

- confirm `OPENSEARCH_INITIAL_ADMIN_PASSWORD` is set
- confirm Docker has enough memory

If pgAdmin cannot connect:

- make sure you register the server with host `postgres`, not `localhost`, when using pgAdmin inside Docker
