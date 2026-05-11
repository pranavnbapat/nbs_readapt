# NbS ReAdapt — Technical Specification for Developers

**Version:** 1.0  
**Date:** 2026-05-11  
**Audience:** Software engineers, DevOps, data engineers  
**Status:** Production-ready (v1)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Data Layer](#4-data-layer)
5. [Application Layer](#5-application-layer)
6. [Search Layer](#6-search-layer)
7. [AI Assistant Layer](#7-ai-assistant-layer)
8. [Frontend Architecture](#8-frontend-architecture)
9. [API Specification](#9-api-specification)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Configuration](#11-configuration)
12. [Development Workflow](#12-development-workflow)
13. [Testing & Quality](#13-testing--quality)
14. [Security Considerations](#14-security-considerations)
15. [Performance Considerations](#15-performance-considerations)
16. [Known Limitations & Roadmap](#16-known-limitations--roadmap)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

The application follows a **four-layer architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Django UI & JSON APIs                             │
│  - HTML templates, static assets, REST endpoints            │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: OpenSearch Search Documents                       │
│  - BM25 index (derived, rebuildable)                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: PostgreSQL Repository Data                        │
│  - Normalized records, taxonomies, import batches           │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Source Excel Files                                │
│  - Curated intake material (not serving layer)              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Core Principles

1. **PostgreSQL is the source of truth** — all derived data rebuilds from here
2. **OpenSearch is ephemeral** — can be recreated at any time via management commands
3. **Excel files are intake-only** — never served directly
4. **Schema-aware ingestion** — new sources require code changes, not just file drops
5. **Environment-driven configuration** — no secrets or env-specific values in code

### 1.3 Data Flow

```
Excel Sources → Validate → Import → PostgreSQL → Prepare Docs → OpenSearch → UI/APIs
                  ↓            ↓         ↓            ↓              ↓
              reports    ImportBatch  QA report   JSONL export   search/facets
```

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | Python | 3.12+ | Runtime |
| **Framework** | Django | 5.x | Web framework |
| **API** | Django REST Framework | 3.15+ | API serialization |
| **Database** | PostgreSQL | 16 | Primary data store |
| **Search** | OpenSearch | 3.5.0 | BM25 search index |
| **Cache** | Django caching | — | Bootstrap API caching (5 min) |
| **Frontend** | Vanilla JS | ES6+ | UI interactivity |
| **Maps** | Leaflet | 1.9.4 | Interactive maps |
| **CSS** | Custom CSS | — | Two design systems (reference + legacy) |
| **Containers** | Docker | — | Service isolation |
| **Orchestration** | Docker Compose | — | Local & production stack |
| **Proxy** | Traefik | 3.6.6 | Production reverse proxy |
| **AI Backend** | VLLM / Anthropic | — | LLM inference for assistant |

---

## 3. Project Structure

```
nbs_readapt/
├── config/                     # Django project configuration
│   ├── settings.py             # Main settings (env-driven)
│   ├── urls.py                 # Root URL router
│   ├── wsgi.py                 # WSGI entrypoint
│   └── asgi.py                 # ASGI entrypoint
│
├── apps/                       # Django applications
│   ├── core/                   # Landing page, health endpoint
│   │   ├── views.py
│   │   └── urls.py
│   ├── repository/             # Data models, import, validation, QA
│   │   ├── models.py           # RepositoryRecord, ImportBatch, taxonomies
│   │   ├── admin.py            # Django admin customization
│   │   ├── views.py            # Bootstrap, overview, QA APIs
│   │   ├── services.py         # Import and normalization logic
│   │   ├── validation.py       # Source validation
│   │   ├── qa.py               # QA report generation
│   │   ├── source_specs.py     # Source schema registry
│   │   ├── forms.py            # Admin forms
│   │   └── management/commands/  # CLI commands
│   ├── search/                 # OpenSearch integration
│   │   ├── opensearch.py       # Client setup
│   │   ├── indexing.py         # Document builder
│   │   ├── views.py            # Search query & facet APIs
│   │   └── management/commands/  # Indexing CLI
│   └── assistant/              # AI assistant backend
│       ├── services.py         # RAG orchestration
│       ├── views.py            # Status & chat endpoints
│       └── urls.py
│
├── templates/                  # Django templates
│   ├── base.html               # Base template
│   ├── core/home_reference.html  # Default SPA UI
│   ├── core/home_legacy.html   # Legacy UI
│   └── admin/repository/       # Admin custom templates
│
├── static/                     # Static assets
│   ├── js/app.js               # Monolithic frontend logic (~435KB)
│   ├── css/home_reference.css  # Reference UI styles
│   └── css/app.css             # Legacy UI styles
│
├── docker/                     # Container files
│   └── web/                    # Web container entrypoint
│
├── deploy/                     # Production deployment
│   ├── traefik/                # Traefik stack
│   └── app/                    # App stack compose
│
├── scripts/                    # Helper shell scripts
│   ├── up.sh                   # Start without rebuild
│   ├── rebuild.sh              # Start with rebuild
│   └── refresh_repository_data.sh  # Full data refresh
│
├── initial_input/              # Source Excel files
│   ├── 01_Papers_Report.xlsx
│   ├── 02_Network_Projects.xlsx
│   ├── 03_EU Funded_Projects.xlsx
│   ├── 04_Policies.xlsx
│   └── Core Concept_Key Terms.xlsx
│
├── data/                       # Pipeline outputs
│   └── exports/
│
├── requirements/               # Python dependencies
│   ├── base.txt
│   └── dev.txt
│
├── docs/                       # Documentation (this directory)
├── docker-compose.yml          # Local development stack
├── Dockerfile                  # Web image build
└── manage.py                   # Django management entrypoint
```

---

## 4. Data Layer

### 4.1 Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ImportBatch   │1   *│ RepositoryRecord│*   *│     Country     │
├─────────────────┤◄────┼─────────────────┼────►├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ source_label    │     │ source_dataset  │     │ name (unique)   │
│ notes           │     │ source_uid (UQ) │     │ slug (unique)   │
│ started_at      │     │ title           │     │ country_code    │
│ completed_at    │     │ raw_payload     │     └─────────────────┘
│ records_imported│     │ normalized_pay  │
└─────────────────┘     │ abstract        │     ┌─────────────────┐
                        │ ... (60 fields) │*   *│     Hazard      │
                        │ countries M2M   ├────►├─────────────────┤
                        │ primary_hazards │     │ id (PK)         │
                        │ secondary_hazards     │ name (unique)   │
                        │ primary_nbs_types     │ slug (unique)   │
                        │ secondary_nbs_types   └─────────────────┘
                        └─────────────────┘
                                              ┌─────────────────┐
                                              │    NbsType      │
                                              ├─────────────────┤
                                              │ id (PK)         │
                                              │ name (unique)   │
                                              │ slug (unique)   │
                                              └─────────────────┘
```

### 4.2 Core Models

#### `RepositoryRecord`

The central unified record with ~60 fields. Key design decisions:

| Field | Type | Notes |
|-------|------|-------|
| `source_uid` | `CharField(unique)` | Stable key: `{dataset}:{sheet}:{row_number}` |
| `source_dataset` | `CharField(choices)` | `papers`, `network_projects`, `eu_projects`, `policies` |
| `raw_payload` | `JSONField` | Complete original Excel row |
| `normalized_payload` | `JSONField` | Derived taxonomy/geo metadata |
| `countries` | `ManyToManyField(Country)` | Canonical country links |
| `primary_hazards` | `ManyToManyField(Hazard)` | Canonical hazard links |
| `primary_nbs_types` | `ManyToManyField(NbsType)` | Canonical NbS type links |
| `latitude` / `longitude` | `FloatField` | Map coordinates (nullable) |

#### `ImportBatch`

Tracks import runs:
- `source_label`: human-readable label
- `notes`: operator free-text notes
- `started_at` / `completed_at`: timing
- `records_imported`: count

#### Taxonomy Models (`Country`, `Hazard`, `NbsType`)

- Auto-slugified on save
- Ordered by name
- M2M-linked from `RepositoryRecord`

### 4.3 Database Schema Notes

- Uses `BigAutoField` as default PK
- `RepositoryRecord` ordered by `source_dataset`, `title`
- Geography intentionally not reduced to countries only
- Supports SQLite fallback for simple local testing (not recommended for production)

---

## 5. Application Layer

### 5.1 Apps Overview

| App | Responsibility | Key Files |
|-----|---------------|-----------|
| `core` | Landing page, health check, route dispatch | `views.py`, `urls.py` |
| `repository` | Data ingestion, normalization, QA, admin, bootstrap API | `models.py`, `services.py`, `validation.py`, `qa.py` |
| `search` | OpenSearch client, document building, query/facet APIs | `opensearch.py`, `indexing.py`, `views.py` |
| `assistant` | RAG orchestration, chat endpoint | `services.py`, `views.py` |

### 5.2 Management Commands

#### Repository Commands

| Command | File | Purpose |
|---------|------|---------|
| `validate_repository_sources` | `validation.py` | Check files/sheets/columns/duplicates |
| `import_initial_input --reset` | `services.py` | Import numbered bundle with reset |
| `import_repository_sources` | `services.py` | Registry-driven selective import |
| `report_repository_qa` | `qa.py` | Generate QA comparison report |

#### Search Commands

| Command | File | Purpose |
|---------|------|---------|
| `prepare_search_documents` | `indexing.py` | Export JSONL of search docs |
| `index_repository_records --recreate` | `indexing.py` | Bulk index PostgreSQL → OpenSearch |

### 5.3 Import Pipeline Logic

The `InitialInputImporter` (`services.py`) performs:

1. **Read source specs** from `source_specs.py`
2. **Load Excel** with `openpyxl` / `pandas`
3. **Validate columns** against required set
4. **Normalize per row**:
   - Map source columns to model fields
   - Normalize hazards via keyword matching → canonical `Hazard` records
   - Normalize NbS types → canonical `NbsType` records
   - Normalize countries → canonical `Country` records
   - Classify geography scope → explicit type
   - Approximate centroids for country-level records without coordinates
5. **Create `RepositoryRecord`** with `raw_payload` and M2M links
6. **Create `ImportBatch`** entry

### 5.4 Normalization Strategy

Normalization is **keyword-based pattern matching**, not ML-based:

```python
# Pseudocode for hazard normalization
for canonical_hazard, patterns in HAZARD_PATTERNS.items():
    if any(pattern in source_text.lower() for pattern in patterns):
        link Hazard.objects.get_or_create(name=canonical_hazard)
```

This is idempotent but requires manual extension when new source patterns emerge.

---

## 6. Search Layer

### 6.1 OpenSearch Configuration

```python
# settings.py
OPENSEARCH = {
    "url": env("OPENSEARCH_URL"),
    "username": env("OPENSEARCH_USERNAME", "admin"),
    "password": env("OPENSEARCH_PASSWORD"),
    "index_bm25": env("OPENSEARCH_INDEX_BM25", "nbs_repository_bm25"),
    "index_neural": env("OPENSEARCH_INDEX_NEURAL", "nbs_repository_neural"),
    "ingest_pipeline": env("OPENSEARCH_INGEST_PIPELINE", "nbs_repository_ingest"),
    "hybrid_pipeline": env("OPENSEARCH_HYBRID_PIPELINE", "nbs_repository_hybrid"),
}
```

### 6.2 Index Mapping

The BM25 index stores flattened documents with:
- Text fields: `title`, `search_text`, `abstract`, `summary`, `description`, `keywords`
- Keyword fields: `source_dataset`, `countries`, `geography_type`, `all_hazards`, `all_nbs_types`, `implementation_stage`, `policy_level`
- Numeric fields: `source_year`
- Geo fields: `location` (lat/lon)

### 6.3 Search Query Construction

```python
# Pseudocode from search/views.py
body = {
    "size": size,
    "query": {
        "bool": {
            "filter": [...],   # Exact term filters
            "must": [
                {"multi_match": {
                    "query": q,
                    "fields": ["title^5", "search_text^3", "keywords^2", "abstract^2", "summary^2", "description"],
                    "type": "best_fields",
                    "operator": "or",
                }}
            ] if q else [{"match_all": {}}]
        }
    },
    "sort": ["_score", {"source_year": {"order": "desc", "missing": "_last"}}]
}
```

### 6.4 Facet Aggregation

The facets endpoint runs an aggregation query with `size: 0` (no hits), returning bucket counts for:
- `source_dataset`, `countries`, `geography_type`
- `all_hazards`, `all_nbs_types`
- `implementation_stage`, `policy_level`
- `year_min`, `year_max`

---

## 7. AI Assistant Layer

### 7.1 Architecture

The assistant implements a **Retrieval-Augmented Generation (RAG)** pattern:

```
User Query → OpenSearch BM25 Retrieval → Relevance Scoring → 
Context Building (token budget) → VLLM Chat Completions API → 
Streamed Response + Source Citations
```

### 7.2 Configuration

```python
# settings.py
VLLM = {
    "base_url": env("RUNPOD_VLLM_HOST"),
    "chat_completions_url": env("VLLM_CHAT_COMPLETIONS_URL"),
    "api_key": env("VLLM_API_KEY"),
    "model": env("VLLM_MODEL"),
    "max_model_len": 65535,
}

ASSISTANT = {
    "timeout_seconds": 120,
    "max_history_messages": 6,
    "context_records": 6,
    "context_field_chars": 280,
    "context_record_chars": 1200,
    "max_query_chars": 4000,
    "approx_chars_per_token": 3.2,
    "max_input_tokens": 0,  # 0 = auto-calculate
    "token_safety_margin": 0,
    "response_style_default": "standard",
    "relevance_min_score": 5.0,
}
```

### 7.3 Context Building Algorithm

1. Query OpenSearch BM25 for top-N records (default: 6)
2. Score each record for relevance
3. Filter by `relevance_min_score` (default: 5.0)
4. Build context string:
   - Include title, year, country, and truncated fields (abstract, outcomes, lessons)
   - Truncate each field to `context_field_chars` (280)
   - Truncate each record to `context_record_chars` (1200)
5. Fit context into token budget:
   - Calculate max tokens from model length - query tokens - response margin
   - Trim context to fit
6. Inject into system prompt with grounding instructions

### 7.4 Response Styles

| Style | Description |
|-------|-------------|
| `brief` | 1–2 sentences, direct answer |
| `standard` | Paragraph with explanation |
| `detailed` | Multi-paragraph with examples and nuance |

---

## 8. Frontend Architecture

### 8.1 Design Systems

Two parallel UI implementations exist:

#### Reference UI (Default at `/`)
- **File:** `templates/core/home_reference.html` + `static/css/home_reference.css`
- **Style:** EU FarmBook greens, compact information density, Cormorant Garamond + Barlow typography
- **Behavior:** Single-page app with tab switching via `showTab()`
- **Data:** Bootstrapped from `/repository/bootstrap/`

#### Legacy UI (at `/legacy/`)
- **File:** `templates/core/home_legacy.html` + `static/css/app.css`
- **Style:** Softer greens, glassmorphic panels, editorial feel, Palatino + Georgia typography
- **Behavior:** Similar tabbed interface, older component design

### 8.2 Frontend Data Flow

```
Page Load → fetch('/repository/bootstrap/') → 
Store ALL_RECS, ALL_PINS, ANA in memory → 
All filtering/search/rendering client-side
```

### 8.3 JavaScript Architecture

The frontend is a **single monolithic JS file** (`static/js/app.js`, ~435KB, heavily processed):

- No framework (React/Vue/Angular)
- Vanilla JS with DOM manipulation
- State managed in global variables
- Leaflet for all map instances
- Anthropic API called directly from browser for AI assistant (API key in `sessionStorage`)

### 8.4 Bootstrap API Response Shape

```json
{
  "records": [...],      // Array of shaped record objects
  "pins": [...],         // Array of {lat, lon, id, title, ...}
  "analytics": {
    "totals": {...},
    "dataset_counts": [...],
    "year_histogram": [...],
    "country_counts": [...],
    "hazard_counts": [...],
    "nbs_counts": [...],
    "evidence_matrix": [...]
  }
}
```

---

## 9. API Specification

### 9.1 Repository Endpoints

#### `GET /repository/`
Returns module status.

```json
{
  "module": "repository",
  "status": "scaffolded",
  "initial_input_exists": true
}
```

#### `GET /repository/overview/`
Returns aggregate statistics.

```json
{
  "total_records": 1557,
  "dataset_counts": [
    {"source_dataset": "papers", "doc_count": 410},
    ...
  ],
  "implementation_stage": [...],
  "year_counts": [...]
}
```

#### `GET /repository/qa/?batch_id={id}`
Returns QA report JSON.

#### `GET /repository/records/{pk}/`
Returns full record detail (bootstrap-shaped).

#### `GET /repository/bootstrap/`
Returns full bootstrapped dataset (cached 5 min).

### 9.2 Search Endpoints

#### `GET /search/`
Returns search module status.

```json
{
  "module": "search",
  "status": "ready_for_indexing",
  "opensearch_url": "http://opensearch:9200",
  "bm25_index": "nbs_repository_bm25",
  "neural_index": "nbs_repository_neural"
}
```

#### `GET /search/query/?q={query}&size=20&...`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Keyword query (optional) |
| `size` | int | Max results (default 20, max 100) |
| `source_dataset` | string[] | Filter by dataset (repeatable) |
| `country` | string[] | Filter by country (repeatable) |
| `geography_type` | string[] | Filter by geography type |
| `hazard` | string[] | Filter by hazard |
| `nbs_type` | string[] | Filter by NbS type |
| `implementation_stage` | string[] | Filter by stage |
| `policy_level` | string[] | Filter by policy level |
| `year_gte` | int | Year range start |
| `year_lte` | int | Year range end |

**Response:**

```json
{
  "took_ms": 45,
  "total": 128,
  "hits": [
    {
      "id": "123",
      "score": 12.45,
      "title": "...",
      "source_dataset": "papers",
      "source_year": 2023,
      ...
    }
  ]
}
```

#### `GET /search/facets/?q={query}&...`

Same filter parameters as `/search/query/`. Returns aggregation buckets.

```json
{
  "source_dataset": [{"key": "papers", "doc_count": 410}],
  "countries": [{"key": "Germany", "doc_count": 89}],
  "geography_type": [...],
  "hazards": [...],
  "nbs_types": [...],
  "implementation_stage": [...],
  "policy_level": [...],
  "year_min": 1998,
  "year_max": 2026
}
```

### 9.3 Assistant Endpoints

#### `GET /assistant/status/`

```json
{
  "status": "ok",
  "provider": "vllm",
  "configured": true,
  "model": "meta-llama/Meta-Llama-3-8B-Instruct",
  "response_styles": ["brief", "standard", "detailed"],
  "default_response_style": "standard"
}
```

#### `POST /assistant/chat/`

**Request Body:**

```json
{
  "query": "What are barriers to urban greening?",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "response_style": "detailed"
}
```

**Response:**

```json
{
  "status": "ok",
  "reason": "generated",
  "response_style": "detailed",
  "grounded": true,
  "reply": "Urban greening faces several barriers...",
  "sources": [
    {
      "record_id": 456,
      "title": "...",
      "source_dataset": "papers",
      "source_year": 2022,
      "country_display": "Spain",
      "source_url": "https://...",
      "score": 8.5,
      "summary": "..."
    }
  ]
}
```

### 9.4 Health Endpoint

#### `GET /health/`
Returns HTTP 200 with basic status text.

---

## 10. Deployment Architecture

### 10.1 Local Development Stack

```yaml
# docker-compose.yml (simplified)
services:
  web:
    build: .
    ports: ["${APP_PORT}:8000"]
    volumes: [".:/app"]
    depends_on: [postgres, opensearch]
  
  postgres:
    image: postgres:16
    ports: ["${POSTGRES_PUBLIC_PORT}:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]
  
  pgadmin:
    image: dpage/pgadmin4
    ports: ["${PGADMIN_PORT}:80"]
  
  opensearch:
    image: opensearchproject/opensearch:3.5.0
    ports: ["${OPENSEARCH_PUBLIC_PORT}:9200"]
    environment:
      plugins.security.disabled: "true"
```

**Ports:** 9500 (web), 9501 (postgres), 9502 (pgadmin), 9503 (opensearch), 9504 (opensearch metrics)

### 10.2 Production Stack (Traefik)

**Two-stack model** for separation of concerns:

#### Stack 1: Traefik Proxy (`deploy/traefik/`)
- Traefik v3.6.6 on ports 80/443
- Let's Encrypt TLS auto-provisioning
- Security middlewares (HSTS, compression, redirect-to-https)
- Dashboard with basic auth
- Creates shared Docker network: `nbs_readapt_proxy`

#### Stack 2: Application (`deploy/app/`)
- `web`, `postgres`, `opensearch` services
- Web container joins external `proxy` network
- Traefik labels handle routing:
  ```yaml
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.nbs_readapt.rule=Host(`${APP_DOMAIN}`)"
    - "traefik.http.routers.nbs_readapt.tls.certresolver=letsencrypt"
  ```
- Uses published image: `ghcr.io/pranavnbapat/nbs_readapt:latest`

### 10.3 Build & Push

```bash
# build_and_push_images.sh
docker build -t ghcr.io/pranavnbapat/nbs_readapt:latest .
docker push ghcr.io/pranavnbapat/nbs_readapt:latest
```

### 10.4 Current Production Caveat

The production web container currently runs Django `runserver --insecure` behind Traefik. **Next hardening step:** replace with Gunicorn + WhiteNoise for static files.

---

## 11. Configuration

### 11.1 Environment Variables

All configuration is environment-driven via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_SECRET_KEY` | `dev-only-insecure-key` | Django secret |
| `APP_DEBUG` | `true` | Debug mode |
| `APP_PORT` | `9500` | Local web port |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `POSTGRES_DB` | `nbs_readapt` | Database name |
| `POSTGRES_USER` | `nbs_readapt` | DB user |
| `POSTGRES_PASSWORD` | — | DB password |
| `POSTGRES_HOST` | `postgres` | DB host |
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch endpoint |
| `OPENSEARCH_USERNAME` | `admin` | OS user |
| `OPENSEARCH_PASSWORD` | — | OS password |
| `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | — | Required for OS startup |
| `RUNPOD_VLLM_HOST` | — | VLLM base URL |
| `VLLM_API_KEY` | — | VLLM API key |
| `VLLM_MODEL` | — | Model identifier |
| `ASSISTANT_TIMEOUT_SECONDS` | `120` | LLM timeout |
| `ASSISTANT_CONTEXT_RECORDS` | `6` | Records in context |
| `APP_DOMAIN` | — | Production domain |
| `LETSENCRYPT_EMAIL` | — | TLS cert email |

### 11.2 Settings Module

`config/settings.py` uses a helper:

```python
def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
```

Booleans parsed via `.lower() == "true"`.

---

## 12. Development Workflow

### 12.1 Quick Start

```bash
# 1. Clone and configure
cp .env.sample .env
# edit .env

# 2. Start stack
docker compose up --build -d

# 3. Run migrations
docker compose exec web python manage.py migrate

# 4. Validate & import
docker compose exec web python manage.py validate_repository_sources
docker compose exec web python manage.py import_initial_input --reset

# 5. Build search index
docker compose exec web python manage.py index_repository_records --recreate

# 6. QA
docker compose exec web python manage.py report_repository_qa
```

### 12.2 Helper Scripts

| Script | Use When |
|--------|----------|
| `scripts/up.sh` | Normal code changes (no rebuild) |
| `scripts/rebuild.sh` | Dockerfile/requirements changed |
| `scripts/refresh_repository_data.sh` | Import/indexing logic changed |

### 12.3 Adding a New Source

1. Inspect Excel: worksheet name, ID column, columns, value patterns
2. Add `SourceSpec` to `apps/repository/source_specs.py`
3. Extend normalizer in `apps/repository/services.py`
4. Validate: `validate_repository_sources`
5. Import: `import_repository_sources`
6. Reindex: `index_repository_records --recreate`
7. QA: `report_repository_qa`

---

## 13. Testing & Quality

### 13.1 Current State

- No automated test suite currently implemented
- QA performed via `report_repository_qa` management command
- Manual testing via admin UI and API endpoints

### 13.2 Recommended Testing Strategy

| Layer | Test Type | Tools |
|-------|-----------|-------|
| Models | Unit tests | pytest-django |
| Import pipeline | Integration tests | pytest + fixtures |
| Search APIs | Integration tests | Django test client |
| Assistant | Mocked LLM tests | pytest + unittest.mock |
| Frontend | E2E tests | Playwright |

### 13.3 QA Report Contents

The QA command generates:
- Source row counts vs imported counts per dataset
- Taxonomy sizes (countries, hazards, NbS types)
- Geocoding coverage percentage
- Missing key fields summary
- Discrepancy flags

---

## 14. Security Considerations

| Concern | Current State | Recommendation |
|---------|--------------|----------------|
| **OpenSearch security** | Disabled in local dev | Enable security plugin in production |
| **Django runserver** | Used in production | Replace with Gunicorn |
| **Static files** | Served by Django dev server | Use WhiteNoise or CDN |
| **API keys** | VLLM key in env; Anthropic in client sessionStorage | Rotate regularly; never commit |
| **HTTPS** | Handled by Traefik | Enforce HSTS |
| **CSRF** | Enabled | Maintain for non-API views |
| **SQL injection** | Django ORM protects | Avoid raw SQL |
| **XSS** | Template auto-escaping | Validate any user-generated content |

---

## 15. Performance Considerations

| Area | Current | Bottleneck | Mitigation |
|------|---------|------------|------------|
| Bootstrap API | Returns full dataset (~1,557 records) | Memory & serialization | Cached 5 min; pagination considered for v2 |
| Search | BM25 on OpenSearch | Index size | Single-node OS sufficient for current data |
| Map | All pins loaded client-side | DOM with >2000 pins | Clustering needed at scale |
| Assistant | VLLM API latency | Network + inference | Timeout 120s; async streaming planned |
| Import | Row-by-row Python | Large files | Batch insert optimization possible |

---

## 16. Known Limitations & Roadmap

### 16.1 Current Limitations

1. **No neural/hybrid search** — BM25 only; neural index mapping exists but unused
2. **Django runserver in production** — not hardened for production load
3. **No user authentication** — shortlist stored in localStorage only
4. **No automated tests** — QA is manual/command-driven
5. **Single monolithic JS file** — hard to maintain; no build system
6. **Client-side AI API calls** — Anthropic key in browser (acceptable for demo, not for SaaS)
7. **Approximate geocoding** — Country centroids are not precise locations

### 16.2 Roadmap

| Priority | Feature | Effort |
|----------|---------|--------|
| P1 | Gunicorn + WhiteNoise production setup | Low |
| P1 | Automated test suite (pytest) | Medium |
| P2 | Neural/hybrid search in OpenSearch | Medium |
| P2 | Server-side AI assistant (proxy LLM calls) | Medium |
| P2 | User accounts with persisted shortlists | Medium |
| P3 | Frontend build system (Vite/Webpack) | Medium |
| P3 | Map pin clustering | Low |
| P3 | CSV/JSON bulk export APIs | Low |

---

**Document Owner:** Lead Developer  
**Review Cycle:** Per sprint  
**Next Review:** Post-v1 hardening
