# Data Pipeline

This document explains how data moves from source Excel files into PostgreSQL and then into OpenSearch.

## Pipeline summary

The intended sequence is:

1. validate source files
2. import and normalize into PostgreSQL
3. prepare OpenSearch-ready documents from PostgreSQL
4. ingest documents into OpenSearch
5. run QA against the imported repository

This separation is intentional.

- PostgreSQL is the canonical repository store
- OpenSearch is a derived search store
- source spreadsheets are intake material, not a serving layer

## Current source files

Registered sources are defined in:

- [source_specs.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/source_specs.py)

Current source bundle:

- `01_Papers_Report.xlsx`
- `02_Network_Projects.xlsx`
- `03_EU Funded_Projects.xlsx`
- `04_Policies.xlsx`

## Stage 1: Validate sources

Purpose:

- confirm files exist
- confirm sheets exist
- confirm required columns exist
- report row counts
- report duplicate source IDs

Command:

```bash
docker compose exec web python manage.py validate_repository_sources
```

Optional scoping:

```bash
docker compose exec web python manage.py validate_repository_sources --dataset papers
docker compose exec web python manage.py validate_repository_sources --filename 04_Policies.xlsx
```

Admin workflow:

- open `http://localhost:9500/admin/repository/importbatch/`
- click `Import Sources`
- use `Validate Sources`

## Stage 2: Import to PostgreSQL

### Fixed initial bundle import

Use this when loading the current numbered source bundle:

```bash
docker compose exec web python manage.py import_initial_input --reset
```

What it does:

- reads Excel source rows
- normalizes field names and values
- preserves `raw_payload`
- stores normalized data in `RepositoryRecord`
- links taxonomies
- records the run as an `ImportBatch`

### Registry-driven import

Use this when selecting only part of the registered source registry:

```bash
docker compose exec web python manage.py import_repository_sources --list-sources
docker compose exec web python manage.py import_repository_sources --reset
docker compose exec web python manage.py import_repository_sources --dataset papers --dataset policies
```

Key behavior:

- `source_uid` preserves row identity even if source spreadsheet IDs are duplicated
- duplicated source spreadsheet IDs are allowed and no longer collapse rows

## Stage 3: Prepare OpenSearch documents

Purpose:

- build search-ready documents from normalized PostgreSQL rows
- make the document layer inspectable before indexing

Command:

```bash
docker compose exec web python manage.py prepare_search_documents
```

Default output:

- [data/exports/opensearch_repository_documents.jsonl](/home/pranav/PyCharm/Parveen/nbs_readapt/data/exports)

Useful options:

```bash
docker compose exec web python manage.py prepare_search_documents --dataset papers
docker compose exec web python manage.py prepare_search_documents --limit 25
```

## Stage 4: Ingest into OpenSearch

Purpose:

- create or recreate the BM25 index
- write derived search documents into OpenSearch

Command:

```bash
docker compose exec web python manage.py index_repository_records --recreate
```

Useful options:

```bash
docker compose exec web python manage.py index_repository_records --dataset policies
docker compose exec web python manage.py index_repository_records --batch-size 500
```

Current search mode:

- BM25 only

Not implemented yet:

- neural index population
- hybrid retrieval pipelines

## Stage 5: QA and reconciliation

Purpose:

- compare validated source row counts with imported repository counts
- report taxonomy sizes
- report geocoding coverage
- report missing key fields

Command:

```bash
docker compose exec web python manage.py report_repository_qa
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
```

API endpoint:

- `http://localhost:9500/repository/qa/`

## Current normalization behavior

The importer currently normalizes:

- country aliases and selected pseudo-country values
- hazard labels into a canonical compact hazard taxonomy
- NbS type labels into a canonical compact NbS taxonomy
- geography scope into explicit geography types
- some missing country-level coordinates into approximate country centroids where the source is clearly country-level

## What to do when new Excel files arrive

If the new file matches an existing source shape:

1. place the file in the chosen input directory
2. register it in [source_specs.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/source_specs.py)
3. validate it
4. import it into PostgreSQL
5. rebuild OpenSearch
6. run QA

If the new file has a new schema:

1. register a new source spec
2. extend normalization logic in [services.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/services.py)
3. validate
4. import
5. reindex
6. run QA

Do not index raw Excel data directly into OpenSearch.

## Current operator workflow

Recommended full local workflow:

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py validate_repository_sources
docker compose exec web python manage.py import_initial_input --reset
docker compose exec web python manage.py index_repository_records --recreate
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
```

## Files involved in the pipeline

- [services.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/services.py): import and normalization logic
- [validation.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/validation.py): source validation
- [qa.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/qa.py): post-import QA reporting
- [indexing.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/search/indexing.py): OpenSearch document building
- [import_repository_sources.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/repository/management/commands/import_repository_sources.py): registry-driven import
- [prepare_search_documents.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/search/management/commands/prepare_search_documents.py): document preparation export
- [index_repository_records.py](/home/pranav/PyCharm/Parveen/nbs_readapt/apps/search/management/commands/index_repository_records.py): OpenSearch indexing

## Current known limitations

- some territories and special regional labels still remain in the country taxonomy and may need a product decision
- approximate centroid geocoding is acceptable for map coverage but should not be mistaken for source-precise coordinates
- neural and hybrid search are not implemented yet
