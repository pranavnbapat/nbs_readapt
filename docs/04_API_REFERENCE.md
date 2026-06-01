# NbS ReAdapt — API Reference

**Version:** 1.0  
**Date:** 2026-05-11  
**Base URL:** `https://nbs-readapt.example.com`  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Repository API](#2-repository-api)
3. [Search API](#3-search-api)
4. [Assistant API](#4-assistant-api)
5. [Health & Status](#5-health--status)
6. [Error Handling](#6-error-handling)
7. [Common Objects](#7-common-objects)
8. [OpenSearch Direct API](#8-opensearch-direct-api)

---

## 1. Authentication

### Current State

The v1 API is **publicly accessible** without authentication. No API keys or tokens are required for repository, search, or health endpoints.

### Assistant API

The `/assistant/chat/` endpoint requires the backend assistant provider to be configured via environment variables. The deployment can use either `vllm` or `anthropic` server-side.

### Future

User authentication and rate limiting are planned for v2.

---

## 2. Repository API

### 2.1 Get Repository Status

```http
GET /repository/
```

Returns the repository module status and whether the initial input directory exists.

**Response:**

```json
{
  "module": "repository",
  "status": "scaffolded",
  "initial_input_exists": true
}
```

---

### 2.2 Get Repository Overview

```http
GET /repository/overview/
```

Returns aggregate statistics about the repository contents.

**Response:**

```json
{
  "total_records": 1557,
  "dataset_counts": [
    {"source_dataset": "papers", "doc_count": 410},
    {"source_dataset": "network_projects", "doc_count": 103},
    {"source_dataset": "eu_projects", "doc_count": 275},
    {"source_dataset": "policies", "doc_count": 769}
  ],
  "implementation_stage": [
    {"implementation_stage": "Implementation", "doc_count": 342},
    {"implementation_stage": "Planning", "doc_count": 189},
    {"implementation_stage": "Monitoring", "doc_count": 156},
    {"implementation_stage": "Completed", "doc_count": 98}
  ],
  "year_counts": [
    {"source_year": 2018, "doc_count": 45},
    {"source_year": 2019, "doc_count": 67},
    {"source_year": 2020, "doc_count": 89},
    {"source_year": 2021, "doc_count": 112},
    {"source_year": 2022, "doc_count": 134},
    {"source_year": 2023, "doc_count": 156}
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_records` | integer | Total count of `RepositoryRecord` objects |
| `dataset_counts` | array | Count per `source_dataset` value |
| `implementation_stage` | array | Count per implementation stage (excludes empty) |
| `year_counts` | array | Count per year (uses `publication_year` → `start_year` → `end_year` coalesce) |

---

### 2.3 Get QA Report

```http
GET /repository/qa/?batch_id={batch_id}
```

Returns a quality assurance report comparing source files to imported records.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | integer | No | Filter to a specific import batch. If omitted, uses the latest batch. |

**Response:**

```json
{
  "batch_id": 12,
  "batch_label": "Initial bundle import",
  "generated_at": "2026-05-11T10:30:00Z",
  "source_validation": {
    "papers": {"source_rows": 410, "imported_rows": 410, "duplicates": 0},
    "network_projects": {"source_rows": 103, "imported_rows": 103, "duplicates": 0},
    "eu_projects": {"source_rows": 275, "imported_rows": 275, "duplicates": 0},
    "policies": {"source_rows": 769, "imported_rows": 769, "duplicates": 0}
  },
  "taxonomy_counts": {
    "countries": 42,
    "hazards": 18,
    "nbs_types": 24
  },
  "geocoding_coverage": {
    "with_coordinates": 1245,
    "without_coordinates": 312,
    "coverage_percent": 80.0
  },
  "missing_fields": {
    "papers": {"abstract": 12, "doi": 89},
    "network_projects": {"lessons": 34},
    "policies": {"enforcement_mechanisms": 567}
  },
  "discrepancies": []
}
```

**Note:** Exact response shape depends on `apps/repository/qa.py` implementation. The above is representative.

---

### 2.4 Get Bootstrap Data

```http
GET /repository/bootstrap/
```

Returns the full bootstrapped dataset used by the frontend. **Cached for 5 minutes.**

**Response:**

```json
{
  "records": [
    {
      "id": 1,
      "source_dataset": "papers",
      "source_dataset_display": "Papers",
      "title": "Green roofs for urban heat mitigation...",
      "source_year": 2022,
      "country_display": "Germany",
      "countries": ["Germany"],
      "geography_type": "country",
      "primary_hazards": ["Urban Heat"],
      "primary_nbs_types": ["Green infrastructure"],
      "implementation_stage": "Implementation",
      "abstract": "This study examines...",
      "lessons": "Community engagement is critical...",
      "barriers": "High upfront costs...",
      "enablers": "Municipal subsidies...",
      "source_url": "https://doi.org/10.xxxx/xxxxx",
      "latitude": 51.1657,
      "longitude": 10.4515
    }
  ],
  "pins": [
    {
      "id": 1,
      "lat": 51.1657,
      "lon": 10.4515,
      "title": "Green roofs for urban heat mitigation...",
      "dataset": "papers",
      "hazards": ["Urban Heat"],
      "nbs_types": ["Green infrastructure"]
    }
  ],
  "analytics": {
    "totals": {
      "all": 1557,
      "papers": 410,
      "network_projects": 103,
      "eu_projects": 275,
      "policies": 769
    },
    "dataset_counts": [...],
    "year_histogram": [...],
    "country_counts": [{"key": "Germany", "doc_count": 89}, ...],
    "hazard_counts": [{"key": "Flooding", "doc_count": 345}, ...],
    "nbs_counts": [{"key": "Green infrastructure", "doc_count": 412}, ...],
    "evidence_matrix": [
      {"nbs_type": "Green infrastructure", "hazard": "Urban Heat", "count": 67},
      ...
    ]
  }
}
```

**Fields — Record Object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `source_dataset` | string | Dataset key |
| `source_dataset_display` | string | Human-readable dataset name |
| `title` | string | Record title |
| `source_year` | integer | Year (publication or start) |
| `country_display` | string | Display geography string |
| `countries` | string[] | Canonical country names |
| `geography_type` | string | `country`, `multi_country`, `supranational`, etc. |
| `primary_hazards` | string[] | Canonical hazard names |
| `secondary_hazards` | string[] | Secondary hazards |
| `primary_nbs_types` | string[] | Canonical NbS type names |
| `secondary_nbs_types` | string[] | Secondary NbS types |
| `implementation_stage` | string | Stage string |
| `policy_level` | string | Policy level |
| `abstract` | string | Abstract text |
| `summary` | string | Summary text |
| `description` | string | Description text |
| `lessons` | string | Lessons learned |
| `barriers` | string | Barriers encountered |
| `enablers` | string | Success factors |
| `outcomes_targeted` | string | Targeted outcomes |
| `ecological_impacts` | string | Ecological impact notes |
| `socio_economic_impacts` | string | Socio-economic impact notes |
| `governance_insights` | string | Governance notes |
| `finance_insights` | string | Finance notes |
| `funding_source` | string | Funding source |
| `source_url` | string | Primary URL |
| `source_url_secondary` | string | Secondary URL |
| `doi` | string | DOI |
| `keywords` | string | Keywords |
| `latitude` | float | Map latitude |
| `longitude` | float | Map longitude |

---

### 2.5 Get Record Detail

```http
GET /repository/records/{pk}/
```

Returns a single record in the same shape as bootstrap records.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pk` | integer | Record primary key |

**Response:** Record object (same fields as bootstrap `records[]` items).

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Record not found |

---

## 3. Search API

### 3.1 Get Search Status

```http
GET /search/
```

Returns search module configuration and OpenSearch connection details.

**Response:**

```json
{
  "module": "search",
  "status": "ready_for_indexing",
  "opensearch_url": "http://opensearch:9200",
  "bm25_index": "nbs_repository_bm25",
  "neural_index": "nbs_repository_neural"
}
```

---

### 3.2 Search Query

```http
GET /search/query/?q={query}&size=20&source_dataset={val}&country={val}&...
```

Executes a BM25 keyword search with optional filters.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | — | Keyword query. Omit or empty for match-all. |
| `size` | integer | 20 | Max results (max 100). |
| `source_dataset` | string[] | — | Filter by dataset. Repeatable. |
| `country` | string[] | — | Filter by country. Repeatable. |
| `geography_type` | string[] | — | Filter by geography type. Repeatable. |
| `hazard` | string[] | — | Filter by hazard. Repeatable. |
| `nbs_type` | string[] | — | Filter by NbS type. Repeatable. |
| `implementation_stage` | string[] | — | Filter by stage. Repeatable. |
| `policy_level` | string[] | — | Filter by policy level. Repeatable. |
| `year_gte` | integer | — | Minimum year (inclusive). |
| `year_lte` | integer | — | Maximum year (inclusive). |

**Example Requests:**

```http
# Simple keyword search
GET /search/query/?q=urban+heat

# Filtered search
GET /search/query/?q=green+infrastructure&country=Germany&country=France&hazard=Urban+Heat&year_gte=2020&size=10

# All records for a dataset
GET /search/query/?source_dataset=policies&size=50
```

**Response:**

```json
{
  "took_ms": 45,
  "total": 128,
  "hits": [
    {
      "id": "456",
      "score": 14.32,
      "title": "Green infrastructure planning in European cities",
      "source_dataset": "papers",
      "source_year": 2023,
      "countries": ["Germany", "Netherlands"],
      "geography_type": "multi_country",
      "all_hazards": ["Urban Heat", "Flooding"],
      "all_nbs_types": ["Green infrastructure"],
      "implementation_stage": "Planning",
      "abstract": "This paper examines...",
      "keywords": "green infrastructure, urban planning, climate adaptation",
      "source_url": "https://doi.org/10.xxxx/xxxxx",
      "country_display": "Germany, Netherlands"
    }
  ]
}
```

**Fields — Hit Object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | OpenSearch document ID (record PK as string) |
| `score` | float | BM25 relevance score |
| `title` | string | Record title |
| `source_dataset` | string | Dataset key |
| `source_year` | integer | Year |
| `countries` | string[] | Canonical countries |
| `geography_type` | string | Geography classification |
| `all_hazards` | string[] | All hazards (primary + secondary) |
| `all_nbs_types` | string[] | All NbS types (primary + secondary) |
| `implementation_stage` | string | Stage |
| `policy_level` | string | Policy level |
| `abstract` | string | Abstract |
| `summary` | string | Summary |
| `description` | string | Description |
| `search_text` | string | Concatenated search text (may be present) |
| `keywords` | string | Keywords |
| `source_url` | string | Primary URL |
| `country_display` | string | Display geography |

**Scoring Fields (boosted):**

| Field | Boost |
|-------|-------|
| `title` | 5× |
| `search_text` | 3× |
| `keywords` | 2× |
| `abstract` | 2× |
| `summary` | 2× |
| `description` | 1× |

---

### 3.3 Search Facets

```http
GET /search/facets/?q={query}&source_dataset={val}&country={val}&...
```

Returns aggregation bucket counts for all filter dimensions, respecting the current query and filter context.

**Query Parameters:** Same as `/search/query/` except `size` is not applicable.

**Example Request:**

```http
GET /search/facets/?q=flooding&country=Netherlands
```

**Response:**

```json
{
  "source_dataset": [
    {"key": "papers", "doc_count": 23},
    {"key": "network_projects", "doc_count": 8},
    {"key": "policies", "doc_count": 15}
  ],
  "countries": [
    {"key": "Netherlands", "doc_count": 46},
    {"key": "Belgium", "doc_count": 12}
  ],
  "geography_type": [
    {"key": "country", "doc_count": 38},
    {"key": "multi_country", "doc_count": 8}
  ],
  "hazards": [
    {"key": "Flooding", "doc_count": 46},
    {"key": "Coastal Erosion", "doc_count": 12},
    {"key": "Storms", "doc_count": 8}
  ],
  "nbs_types": [
    {"key": "Blue infrastructure", "doc_count": 28},
    {"key": "Green infrastructure", "doc_count": 18}
  ],
  "implementation_stage": [
    {"key": "Implementation", "doc_count": 22},
    {"key": "Planning", "doc_count": 15},
    {"key": "Monitoring", "doc_count": 9}
  ],
  "policy_level": [
    {"key": "National", "doc_count": 18},
    {"key": "EU", "doc_count": 12}
  ],
  "year_min": 2005,
  "year_max": 2025
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `source_dataset` | bucket[] | Dataset distribution |
| `countries` | bucket[] | Country distribution (top 100) |
| `geography_type` | bucket[] | Geography type distribution |
| `hazards` | bucket[] | Hazard distribution (top 100) |
| `nbs_types` | bucket[] | NbS type distribution (top 100) |
| `implementation_stage` | bucket[] | Stage distribution |
| `policy_level` | bucket[] | Policy level distribution |
| `year_min` | float | Minimum year in result set |
| `year_max` | float | Maximum year in result set |

**Bucket Object:**

```json
{"key": "Germany", "doc_count": 89}
```

---

## 4. Assistant API

### 4.1 Get Assistant Status

```http
GET /assistant/status/
```

Returns assistant configuration and availability.

**Response:**

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

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or error state |
| `provider` | string | LLM provider identifier |
| `configured` | boolean | Whether the selected assistant provider is fully configured |
| `model` | string | Model identifier |
| `response_styles` | string[] | Available response styles |
| `default_response_style` | string | Default style |

---

### 4.2 Chat

```http
POST /assistant/chat/
```

Sends a user query and receives an AI-generated answer grounded in repository records.

**Request Headers:**

```http
Content-Type: application/json
```

**Request Body:**

```json
{
  "query": "What are the main barriers to urban green infrastructure?",
  "history": [
    {"role": "user", "content": "Tell me about green roofs"},
    {"role": "assistant", "content": "Green roofs are..."}
  ],
  "response_style": "detailed"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | User question (max ~4000 chars) |
| `history` | message[] | No | Previous conversation turns |
| `response_style` | string | No | `"brief"`, `"standard"`, or `"detailed"` |

**Message Object:**

```json
{"role": "user|assistant", "content": "string"}
```

**Response (Success):**

```json
{
  "status": "ok",
  "reason": "generated",
  "response_style": "detailed",
  "grounded": true,
  "reply": "Urban green infrastructure faces several barriers...",
  "sources": [
    {
      "record_id": 123,
      "title": "Barriers to green roof adoption in European cities",
      "source_dataset": "papers",
      "source_year": 2021,
      "country_display": "Germany",
      "source_url": "https://doi.org/10.xxxx/xxxxx",
      "score": 8.7,
      "summary": "This study identifies financial, regulatory, and social barriers..."
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or `"error"` |
| `reason` | string | Generation reason (e.g., `"generated"`, `"no_results"`) |
| `response_style` | string | Applied response style |
| `grounded` | boolean | Whether answer is grounded in retrieved records |
| `reply` | string | AI-generated answer text |
| `sources` | source[] | Cited grounding records |

**Source Object:**

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | integer | RepositoryRecord PK |
| `title` | string | Record title |
| `source_dataset` | string | Dataset key |
| `source_year` | integer | Year |
| `country_display` | string | Geography string |
| `source_url` | string | URL to original document |
| `score` | float | Relevance score (0–10+) |
| `summary` | string | Truncated record summary |

**Error Responses:**

| Status | Body | Cause |
|--------|------|-------|
| 400 | `{"status":"error","error":"Invalid JSON body."}` | Malformed JSON |
| 400 | `{"status":"error","error":"Query is required."}` | Empty query |
| 400 | `{"status":"error","error":"..."}` | ValueError from service |
| 502 | `{"status":"error","error":"..."}` | LLM service unavailable |

---

## 5. Health & Status

### 5.1 Health Check

```http
GET /health/
```

Simple health endpoint for load balancers and monitoring.

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: text/plain

ok
```

---

## 6. Error Handling

### 6.1 HTTP Status Codes

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| 200 | OK | Successful GET/POST |
| 400 | Bad Request | Invalid parameters, missing fields |
| 404 | Not Found | Record does not exist |
| 405 | Method Not Allowed | Wrong HTTP method |
| 502 | Bad Gateway | LLM service unavailable |
| 500 | Internal Server Error | Unhandled exception |

### 6.2 Error Response Format

All JSON error responses follow this shape:

```json
{
  "status": "error",
  "error": "Human-readable error message"
}
```

### 6.3 Validation Errors

For validation failures (e.g., invalid year format), the error message describes the specific issue:

```json
{
  "status": "error",
  "error": "Invalid year_gte: expected integer"
}
```

---

## 7. Common Objects

### 7.1 Dataset Values

| Value | Display Name |
|-------|-------------|
| `papers` | Papers |
| `network_projects` | Network Projects |
| `eu_projects` | EU Funded Projects |
| `policies` | Policies |

### 7.2 Geography Type Values

| Value | Description |
|-------|-------------|
| `country` | Single country |
| `multi_country` | Multiple countries |
| `supranational` | EU, continental, or global scope |
| `transnational_region` | Cross-border regions (e.g., Alps, Danube basin) |
| `global` | Worldwide |
| `local_place` | City, municipality, or site |
| `unknown` | Undetermined |

### 7.3 Response Style Values

| Value | Description |
|-------|-------------|
| `brief` | Concise, 1–2 sentences |
| `standard` | Paragraph with explanation |
| `detailed` | Multi-paragraph with examples |

---

## 8. OpenSearch Direct API

For advanced use cases, you may query OpenSearch directly. The local development endpoint is:

```
http://localhost:9503/
```

### 8.1 Check Indices

```bash
curl -sS http://localhost:9503/_cat/indices?v
```

### 8.2 Search Directly

```bash
curl -X POST "http://localhost:9503/nbs_repository_bm25/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 10,
    "query": {
      "multi_match": {
        "query": "flooding",
        "fields": ["title^5", "search_text^3", "abstract^2"]
      }
    }
  }'
```

### 8.3 Important Notes

- The OpenSearch security plugin is **disabled in local development**
- In production, authentication is required
- Do not modify the index mapping without updating the Django indexing code
- Always prefer the Django `/search/` API over direct OpenSearch queries for application use

---

**Document Owner:** API Lead  
**Review Cycle:** Per release  
**Last Updated:** 2026-05-11
