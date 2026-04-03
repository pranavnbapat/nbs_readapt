# Architecture

This document explains how the project is structured and how the main components work together.

## High-level architecture

The application has four layers:

1. Source files
2. PostgreSQL repository data
3. OpenSearch search documents
4. Django UI and JSON APIs

Principles:

- PostgreSQL is the source of truth
- OpenSearch is a derived search layer
- source Excel files are never treated as the serving layer
- the UI should consume backend APIs, not hard-coded embedded data

## Source inputs

Primary source files live in:

- [initial_input](/home/pranav/PyCharm/Parveen/nbs_readapt/initial_input)

Current numbered sources:

- `01_Papers_Report.xlsx`
- `02_Network_Projects.xlsx`
- `03_EU Funded_Projects.xlsx`
- `04_Policies.xlsx`

Reference-only prototype files:

- `index.html`
- `index_ai.html`

These HTML files are treated as functional and design references, not as production architecture.

## Service architecture

### `web`

The Django application container handles:

- HTML page rendering
- repository and search APIs
- admin interface
- import, validation, indexing, and QA management commands

### `postgres`

PostgreSQL stores:

- normalized repository records
- import batch records
- taxonomy tables

### `opensearch`

OpenSearch stores:

- BM25 search index documents derived from PostgreSQL

### `pgadmin`

pgAdmin is included as an operator tool for:

- inspecting tables
- running ad hoc SQL
- validating import outcomes

## Django project structure

Main directories:

- [config](/home/pranav/PyCharm/Parveen/nbs_readapt/config): Django settings and root URL config
- [apps/core](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/core): landing page and health endpoints
- [apps/repository](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository): repository models, import logic, validation, QA, admin
- [apps/search](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/search): OpenSearch document building, indexing, and search endpoints
- [templates](/home/pranav/PyCharm/Parveen/nbs_readapt/templates): Django templates
- [static](/home/pranav/PyCharm/Parveen/nbs_readapt/static): CSS and JavaScript assets
- [docker](/home/pranav/PyCharm/Parveen/nbs_readapt/docker): container entrypoint files
- [requirements](/home/pranav/PyCharm/Parveen/nbs_readapt/requirements): Python dependency sets

## Repository data model

Core model:

- `RepositoryRecord`

Supporting models:

- `ImportBatch`
- `Country`
- `Hazard`
- `NbsType`

Important design choices:

- every imported row gets a stable `source_uid`
- raw source rows are preserved in `raw_payload`
- normalized fields are preserved in `normalized_payload`
- taxonomy relationships are explicit M2M links
- duplicated source spreadsheet IDs do not overwrite rows anymore

## Data flow

### 1. Source validation

The system validates:

- file existence
- sheet existence
- required columns
- row counts
- duplicate source IDs

### 2. Import and normalization

The importer:

- reads the registered source specs
- maps source fields into the unified repository schema
- normalizes hazards, NbS types, countries, and geography
- records import metadata in `ImportBatch`

### 3. Search document preparation

The search layer:

- reads normalized PostgreSQL records
- builds search text
- builds facet fields
- derives geography metadata
- exports JSONL when needed

### 4. OpenSearch indexing

The indexer:

- creates or recreates the BM25 index
- streams documents from PostgreSQL
- writes documents into OpenSearch

### 5. UI and API serving

The frontend uses backend APIs for:

- query results
- facet lists
- overview analytics
- repository QA
- record detail hydration

## Geography model

Geography is intentionally not reduced to countries only.

Search documents now distinguish:

- `country`
- `multi_country`
- `supranational`
- `transnational_region`
- `global`
- `local_place`
- `unknown`

This prevents EU-wide or basin-level records from being forced incorrectly into the country taxonomy.

## Taxonomy normalization

Current importer normalizes:

- hazard labels into a compact canonical hazard set
- NbS type labels into a compact canonical NbS set
- country aliases and pseudo-country labels where possible

This keeps PostgreSQL taxonomies and OpenSearch facets usable.

## Frontend structure

Main UI entrypoint:

- [home.html](/home/pranav/PyCharm/Parveen/nbs_readapt/templates/core/home.html)

Main frontend assets:

- [app.css](/home/pranav/PyCharm/Parveen/nbs_readapt/static/css/app.css)
- [app.js](/home/pranav/PyCharm/Parveen/nbs_readapt/static/js/app.js)

Current UI sections:

- search and browse
- map
- analytics
- shortlist drawer
- record detail modal

## Search API structure

Search endpoints currently support:

- keyword search
- source dataset filtering
- country filtering
- geography type filtering
- hazard filtering
- NbS type filtering
- implementation stage filtering
- policy level filtering
- year range filtering

Current search mode:

- BM25 only

Not implemented yet:

- neural search
- hybrid search
- AI assistant

## Operational philosophy

This codebase is structured for handover:

- Dockerized local stack
- environment-driven configuration
- Django admin for operators
- management commands for repeatable workflows
- explicit markdown docs for operations and data pipeline
