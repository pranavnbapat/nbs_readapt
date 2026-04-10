# NbS ReAdapt

Repository application for the NbS ReAdapt knowledge base.

This project rebuilds the original HTML prototype as a Dockerized Django application backed by PostgreSQL and OpenSearch.

## What this project does

- imports curated Excel source files into PostgreSQL
- normalizes records into a unified repository schema
- builds a derived OpenSearch search index from PostgreSQL
- serves a search, map, and analytics UI
- exposes backend JSON endpoints for repository and search workflows
- provides admin-assisted import, validation, and QA workflows

## Current stack

- Django
- Django REST Framework
- PostgreSQL 16
- OpenSearch 3.5.0
- pgAdmin 4
- Docker Compose

## Documentation map

- [OPERATIONS.md](/home/pranav/PyCharm/Parveen/nbs_readapt/OPERATIONS.md): how to run the stack, access the app, admin, DB, and OpenSearch
- [PIPELINE.md](/home/pranav/PyCharm/Parveen/nbs_readapt/PIPELINE.md): source intake, normalization, indexing, and QA pipeline
- [ARCHITECTURE.md](/home/pranav/PyCharm/Parveen/nbs_readapt/ARCHITECTURE.md): project structure, service responsibilities, and data flow
- [PORTS.md](/home/pranav/PyCharm/Parveen/nbs_readapt/PORTS.md): host-port policy and assignments
- [CHECKLIST.md](/home/pranav/PyCharm/Parveen/nbs_readapt/CHECKLIST.md): delivery status and remaining work
- [ASSESSMENT.md](/home/pranav/PyCharm/Parveen/nbs_readapt/ASSESSMENT.md): historical context and scope shift from `readapt`

## Quick start

1. Copy `.env.sample` to `.env` if needed and review credentials.
2. Start the stack:

```bash
docker compose up --build -d
```

3. Run Django migrations:

```bash
docker compose exec web python manage.py migrate
```

4. Validate source files:

```bash
docker compose exec web python manage.py validate_repository_sources
```

5. Import source files into PostgreSQL:

```bash
docker compose exec web python manage.py import_initial_input --reset
```

6. Build the OpenSearch index:

```bash
docker compose exec web python manage.py index_repository_records --recreate
```

7. Generate a QA report:

```bash
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
```

## Adding new Excel data

Use Excel as the intake path. Do not use pgAdmin for normal data ingestion.

Short operator flow:

1. place the new Excel file in the chosen input directory
2. confirm whether it matches an existing registered source shape
3. if it matches, register/select it and validate it
4. if it does not match, add a new source spec and extend the normalizer first
5. import into PostgreSQL
6. rebuild the OpenSearch index
7. run QA

Operator commands:

```bash
docker compose exec web python manage.py validate_repository_sources
docker compose exec web python manage.py import_repository_sources
docker compose exec web python manage.py prepare_search_documents
docker compose exec web python manage.py index_repository_records --recreate
docker compose exec web python manage.py report_repository_qa
```

Important rule:

- new Excel files should follow a known schema or column structure if you want no-code ingestion
- if the file uses a new column layout, naming convention, worksheet name, or value pattern, the importer must be updated first

See [PIPELINE.md](/home/pranav/PyCharm/Parveen/nbs_readapt/PIPELINE.md) for the detailed SOP and schema expectations.

## Main URLs

- App UI: `http://localhost:9500/`
- Django admin: `http://localhost:9500/admin/`
- Health endpoint: `http://localhost:9500/health/`
- Repository overview API: `http://localhost:9500/repository/overview/`
- Repository QA API: `http://localhost:9500/repository/qa/`
- Search query API: `http://localhost:9500/search/query/?q=flooding`
- Search facets API: `http://localhost:9500/search/facets/`
- pgAdmin: `http://localhost:9502/`
- OpenSearch API: `http://localhost:9503/`

## Current application status

Implemented:

- unified repository schema
- import validation and admin-assisted imports
- PostgreSQL source-of-truth data layer
- OpenSearch BM25 index
- search, facets, map, analytics, shortlist, and detail modal UI
- post-import QA reporting
- geography-aware search facets
- normalized hazard, NbS, and country taxonomies

Not implemented yet:

- server-side AI assistant
- neural or hybrid search
- deployment-grade reverse proxy and production hardening
- setup/handover automation shell scripts

## Notes

- All host-facing ports stay in the `9500-9599` range.
- PostgreSQL is the source of truth.
- OpenSearch is derived and can be rebuilt from PostgreSQL at any time.
- `readapt` is historical reference only. Active work is in `nbs_readapt`.
