# NbS ReAdapt — Functional Requirements Document (FRD)

**Version:** 1.0  
**Date:** 2026-05-11  
**Project:** NbS ReAdapt Knowledge Repository  
**Status:** Production-ready (v1) with planned v2 enhancements  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Project Overview](#2-project-overview)
3. [Stakeholders & Users](#3-stakeholders--users)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 [Data Ingestion & Management](#41-data-ingestion--management)
   - 4.2 [Search & Discovery](#42-search--discovery)
   - 4.3 [Evidence Mapping](#43-evidence-mapping)
   - 4.4 [Analytics & Reporting](#44-analytics--reporting)
   - 4.5 [AI Assistant](#45-ai-assistant)
   - 4.6 [Policy Explorer](#46-policy-explorer)
   - 4.7 [Shortlist & Briefing Generation](#47-shortlist--briefing-generation)
   - 4.8 [Administration & QA](#48-administration--qa)
5. [User Stories](#5-user-stories)
6. [Data Requirements](#6-data-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Glossary](#8-glossary)

---

## 1. Introduction

### 1.1 Purpose

This Functional Requirements Document (FRD) defines the complete set of functional requirements for the **NbS ReAdapt Knowledge Repository** — a web-based platform that curates, organizes, and serves evidence on Nature-based Solutions (NbS) for climate adaptation across Europe. The platform supports researchers, policymakers, practitioners, and project managers in discovering relevant evidence, comparing cases, and generating actionable insights.

### 1.2 Scope

This document covers:
- End-user functionality accessible via the web interface
- Backend data ingestion, normalization, and quality assurance workflows
- Search, browse, map, analytics, and AI-assisted discovery features
- Administrative and operational capabilities

Out of scope for this version:
- Neural/hybrid search (planned for v2)
- User authentication and role-based access control (future enhancement)
- Multi-language UI support

### 1.3 Definitions & Acronyms

| Term | Definition |
|------|------------|
| **NbS** | Nature-based Solutions — actions to protect, sustainably manage, and restore natural or modified ecosystems |
| **BM25** | Best Match 25 — a ranking function used in information retrieval |
| **OpenSearch** | Open-source search and analytics engine (fork of Elasticsearch) |
| **Source UID** | Stable unique identifier for each imported record (`dataset:sheet:row_number`) |
| **M2M** | Many-to-Many (database relationship) |
| **VLLM** | Virtual Large Language Model serving framework |
| **RAG** | Retrieval-Augmented Generation |

---

## 2. Project Overview

### 2.1 Background

The ESPON ReAdapt project requires a centralized knowledge repository to aggregate evidence from four distinct source categories:
1. Academic papers and reports
2. Network projects (case studies)
3. EU-funded projects
4. Policies (EU and national-level)

The repository must normalize heterogeneous source data into a unified schema, enable powerful search and discovery, and provide visual analytics to identify evidence gaps.

### 2.2 High-Level Objectives

| ID | Objective |
|----|-----------|
| O1 | Provide a single, searchable repository of NbS evidence across all source types |
| O2 | Enable geographic discovery through interactive mapping |
| O3 | Support evidence-based decision-making through analytics and gap analysis |
| O4 | Offer AI-assisted Q&A grounded in repository content |
| O5 | Ensure data quality through validation, normalization, and QA workflows |
| O6 | Support export and briefing generation for end-users |

### 2.3 Current Dataset Summary

| Dataset | Records | Type |
|---------|---------|------|
| Papers & Reports | ~410 | Academic literature |
| Network Projects | ~103 | Case studies |
| EU Funded Projects | ~275 | Funding programme records |
| Policies | ~769 | Legal/policy documents |
| **Total** | **~1,557** | — |

---

## 3. Stakeholders & Users

### 3.1 User Roles

| Role | Description | Primary Needs |
|------|-------------|---------------|
| **Researcher** | Academic or policy researcher investigating NbS evidence | Deep search, filtering, record detail, citations |
| **Policymaker** | Government or EU official crafting climate adaptation policy | Policy explorer, gap analysis, comparable cases |
| **Practitioner** | On-the-ground project manager implementing NbS | Practical case studies, lessons learned, implementation stages |
| **Project Manager** | Coordinator of EU-funded or network projects | Funding sources, comparable projects, outcomes |
| **Data Operator** | Technical staff maintaining the repository | Import, validation, QA, reindexing workflows |
| **System Administrator** | DevOps/IT staff managing deployment | Monitoring, backups, scaling, troubleshooting |

### 3.2 User Personas

#### Persona 1: Dr. Elena Varga — Climate Adaptation Researcher
- **Background:** Environmental scientist at a European research institute
- **Goals:** Find peer-reviewed evidence on urban heat island NbS interventions in Southern Europe
- **Pain Points:** Evidence scattered across databases; difficulty comparing studies across countries
- **Needs:** Advanced filtering, full-text search, evidence density maps, export for systematic reviews

#### Persona 2: Marcus Johansson — EU Policy Advisor
- **Background:** Works in DG CLIMA, drafting the next EU Adaptation Strategy
- **Goals:** Identify policy gaps in NbS coverage for flooding and coastal hazards
- **Pain Points:** No single view of existing policies; hard to compare binding vs non-binding instruments
- **Needs:** Policy explorer, gap analysis, legal bindingness filters, briefing generation

#### Persona 3: Sofia Costa — Municipal NbS Project Manager
- **Background:** Runs a green infrastructure project in Lisbon
- **Goals:** Learn from similar projects, understand barriers and enablers
- **Pain Points:** Academic papers too theoretical; case studies hard to find
- **Needs:** Practitioner view, lessons learned, comparable cases, shortlist for reporting

---

## 4. Functional Requirements

---

### 4.1 Data Ingestion & Management

#### FR-DI-001: Excel Source Registration
**Priority:** Must-have  
**Description:** The system shall support registering Excel source files with defined schemas (SourceSpec) including filename, worksheet name, ID column, required columns, and normalizer key.  
**Acceptance Criteria:**
- Each source must have a unique filename and dataset key
- Required columns must be validated before import
- Schema changes require code updates in `source_specs.py`

#### FR-DI-002: Source Validation
**Priority:** Must-have  
**Description:** The system shall validate source files before import, checking file existence, sheet existence, required columns, row counts, and duplicate source IDs.  
**Acceptance Criteria:**
- Validation reports row counts per source
- Validation flags duplicate `source_record_id` values
- Validation can be scoped by dataset or filename
- Admin UI provides "Validate Sources" button

#### FR-DI-003: Import with Normalization
**Priority:** Must-have  
**Description:** The system shall import validated Excel rows into PostgreSQL, normalizing fields, linking taxonomies, and preserving raw source data.  
**Acceptance Criteria:**
- Each row receives a stable `source_uid` (`dataset:sheet:row_number`)
- Raw payload preserved in `raw_payload` JSON field
- Normalized metadata stored in `normalized_payload` JSON field
- Taxonomies (Country, Hazard, NbS Type) linked via M2M relationships
- Geography scope classified into: `country`, `multi_country`, `supranational`, `transnational_region`, `global`, `local_place`, `unknown`
- Import runs recorded in `ImportBatch` with timestamp and record count

#### FR-DI-004: Taxonomy Normalization
**Priority:** Must-have  
**Description:** The system shall normalize heterogeneous source values into canonical taxonomies.  
**Acceptance Criteria:**
- Hazard labels normalized to canonical compact set (e.g., Flooding, Wildfires, Drought, Urban Heat, etc.)
- NbS type labels normalized to canonical set (e.g., Green infrastructure, Blue infrastructure, Forest restoration, etc.)
- Country aliases and pseudo-country labels mapped to canonical `Country` records
- New taxonomy values handled gracefully (created or mapped)

#### FR-DI-005: Duplicate Handling
**Priority:** Must-have  
**Description:** The system shall allow duplicate source spreadsheet IDs without collapsing rows.  
**Acceptance Criteria:**
- Duplicate `source_record_id` values do not overwrite existing records
- Each imported row is treated as a distinct record with unique `source_uid`

#### FR-DI-006: Reindexing on Data Change
**Priority:** Must-have  
**Description:** When repository data changes in PostgreSQL, the OpenSearch index must be rebuildable.  
**Acceptance Criteria:**
- Management command `index_repository_records --recreate` recreates the BM25 index
- Indexing streams documents from PostgreSQL in batches
- Search results reflect updated data within minutes of reindexing

---

### 4.2 Search & Discovery

#### FR-SD-001: Full-Text Keyword Search
**Priority:** Must-have  
**Description:** Users shall search across all record fields using keywords with BM25 relevance scoring.  
**Acceptance Criteria:**
- Search queries match title (boosted 5×), search_text (3×), keywords (2×), abstract, summary, and description
- Empty query returns all results (match_all)
- Results sorted by relevance score, then by year descending
- Response includes total count, took_ms, and hit array

#### FR-SD-002: Faceted Filtering
**Priority:** Must-have  
**Description:** Users shall filter search results by multiple dimensions simultaneously.  
**Acceptance Criteria:**
- Available filters: source dataset, country, geography type, hazard, NbS type, implementation stage, policy level, year range
- Multiple values within a filter use OR logic
- Different filters use AND logic
- Filter counts update dynamically based on current query context

#### FR-SD-003: Facet Aggregation API
**Priority:** Must-have  
**Description:** The system shall provide facet bucket counts for all filter dimensions.  
**Acceptance Criteria:**
- `/search/facets/` returns aggregation buckets for all filterable fields
- Facets respect current query and filter context
- Year min/max returned as range boundaries
- Buckets include key and doc_count

#### FR-SD-004: Record Detail View
**Priority:** Must-have  
**Description:** Users shall view complete record details in a modal or dedicated page.  
**Acceptance Criteria:**
- Detail view shows all 60+ fields when populated
- Taxonomy tags displayed as clickable pills
- Source URL(s) presented as active links
- Raw metadata available for transparency

#### FR-SD-005: Practitioner View Toggle
**Priority:** Should-have  
**Description:** Search results shall support a "Practitioner View" that surfaces lessons learned, barriers, and enablers.  
**Acceptance Criteria:**
- Toggle switches result card layout
- Practitioner view auto-expands lessons/barriers/enablers fields
- Regular view shows standard metadata (title, year, country, abstract)

#### FR-SD-006: Bootstrap API for Client-Side Search
**Priority:** Must-have  
**Description:** The UI shall receive a bootstrapped dataset for responsive client-side filtering.  
**Acceptance Criteria:**
- `/repository/bootstrap/` returns records, map pins, and analytics
- Response cached for 5 minutes
- All subsequent filtering performed client-side for speed

---

### 4.3 Evidence Mapping

#### FR-EM-001: Interactive Leaflet Map
**Priority:** Must-have  
**Description:** The system shall display geolocated records on an interactive map using Leaflet.js.  
**Acceptance Criteria:**
- Map uses OpenStreetMap base tiles
- Records shown as pins at lat/lon coordinates
- Country-level records use approximate centroids when exact coordinates unavailable
- Clicking a pin opens record detail

#### FR-EM-002: Map Filtering
**Priority:** Must-have  
**Description:** Users shall filter map pins by NbS type, hazard, and domain.  
**Acceptance Criteria:**
- Filter changes update pin visibility in real-time
- Filter state synchronized with Search & Browse tab

#### FR-EM-003: Choropleth Overlay
**Priority:** Should-have  
**Description:** The map shall support choropleth overlays showing record density by country.  
**Acceptance Criteria:**
- "Country Coverage" mode colors countries by record count
- Legend explains color scale
- Clicking a country navigates to search filtered by that country

#### FR-EM-004: Pin Coloring Modes
**Priority:** Should-have  
**Description:** Map pins shall be colorable by NbS type or hazard.  
**Acceptance Criteria:**
- Color mode toggle switches legend and pin colors
- Each taxonomy value assigned a consistent color

---

### 4.4 Analytics & Reporting

#### FR-AR-001: Overview Metrics
**Priority:** Must-have  
**Description:** The analytics dashboard shall display high-level repository metrics.  
**Acceptance Criteria:**
- Total record count
- Counts per dataset (papers, cases, EU projects, policies)
- Implementation stage distribution
- Year histogram

#### FR-AR-002: Choropleth Analytics Maps
**Priority:** Should-have  
**Description:** The analytics tab shall display hazard-by-country and NbS-type-by-country choropleth mini-maps.  
**Acceptance Criteria:**
- Maps show relative density with ranking sidebars
- Hover shows exact counts
- Click navigates to filtered search

#### FR-AR-003: Evidence Density Matrix
**Priority:** Should-have  
**Description:** The system shall display a matrix of NbS types vs. hazards showing record counts.  
**Acceptance Criteria:**
- Matrix cells show record count
- Toggle between count and percentage views
- Clicking a cell filters search to that intersection

#### FR-AR-004: Country Deep-Dive
**Priority:** Should-have  
**Description:** Users shall view detailed statistics for a selected country.  
**Acceptance Criteria:**
- Modal shows country name, total records, dataset breakdown
- Top hazards and NbS types listed
- Link to browse all records for that country

#### FR-AR-005: Research Gap Analysis
**Priority:** Should-have  
**Description:** The system shall identify and display under-researched NbS–hazard combinations.  
**Acceptance Criteria:**
- Gap matrix highlights cells with <3 records in red
- Priority gap list sorted by research deficit
- Gaps computed live from current dataset

---

### 4.5 AI Assistant

#### FR-AI-001: Assistant Status Endpoint
**Priority:** Must-have  
**Description:** The system shall report assistant configuration and availability.  
**Acceptance Criteria:**
- `/assistant/status/` returns provider, model, configured flag, and supported response styles

#### FR-AI-002: Retrieval-Augmented Chat
**Priority:** Must-have  
**Description:** Users shall ask natural language questions and receive answers grounded in repository records.  
**Acceptance Criteria:**
- Query processed via POST to `/assistant/chat/`
- System queries OpenSearch for relevant records using BM25
- Retrieved records scored for relevance
- Context block built from top-N records, truncated to token budget
- VLLM API called with grounded system prompt
- Response includes reply text and source citations

#### FR-AI-003: Response Styles
**Priority:** Should-have  
**Description:** The assistant shall support multiple response styles.  
**Acceptance Criteria:**
- Styles: `brief`, `standard`, `detailed`
- Style selectable per query
- Default style configurable via environment

#### FR-AI-004: Source Citations
**Priority:** Must-have  
**Description:** Assistant responses shall include citations to grounding records.  
**Acceptance Criteria:**
- Each source shows title, dataset, year, country, URL, and relevance score
- Sources linkable to record detail
- Maximum context records configurable (default: 6)

#### FR-AI-005: Conversation History
**Priority:** Should-have  
**Description:** The assistant shall maintain conversation history within a session.  
**Acceptance Criteria:**
- History sent with each query
- History truncated to configurable max messages (default: 6)
- History managed client-side

---

### 4.6 Policy Explorer

#### FR-PE-001: Dedicated Policy Browser
**Priority:** Must-have  
**Description:** The system shall provide a dedicated interface for browsing all 769+ policy records.  
**Acceptance Criteria:**
- Sidebar filters: country, legal bindingness, NbS type, hazard, text search
- Result cards optimized for policy metadata (level, bindingness, year)
- CSV export of filtered results

#### FR-PE-002: Policy-Level Filtering
**Priority:** Must-have  
**Description:** Users shall filter policies by policy level (EU, national, regional, local).  
**Acceptance Criteria:**
- Multi-select policy level filter
- Filter reflected in URL/state for sharing

#### FR-PE-003: Bindingness Classification
**Priority:** Should-have  
**Description:** Policies shall display and be filterable by legal bindingness.  
**Acceptance Criteria:**
- Binding, non-binding, and mixed classifications supported
- Filterable via sidebar

---

### 4.7 Shortlist & Briefing Generation

#### FR-SB-001: Shortlist Management
**Priority:** Must-have  
**Description:** Users shall build a personal shortlist of records across sessions.  
**Acceptance Criteria:**
- "+" button on each record adds to shortlist
- Shortlist persisted in browser (localStorage)
- Shortlist drawer slides in from side
- Remove individual items or clear all
- Shortlist count badge updates in real-time

#### FR-SB-002: Briefing Generation
**Priority:** Should-have  
**Description:** Users shall generate a styled HTML briefing document from their shortlist.  
**Acceptance Criteria:**
- "Generate Briefing" button opens styled HTML document
- Briefing includes summary, tag analysis, and detailed record blocks
- Print-friendly styling for PDF export
- Records ordered as in shortlist

---

### 4.8 Administration & QA

#### FR-AD-001: Django Admin Interface
**Priority:** Must-have  
**Description:** Operators shall manage records, taxonomies, and import batches via Django Admin.  
**Acceptance Criteria:**
- Admin at `/admin/`
- ImportBatch list with notes and timestamps
- RepositoryRecord searchable and filterable
- Country, Hazard, NbSType editable

#### FR-AD-002: Import Sources Admin Workflow
**Priority:** Must-have  
**Description:** Operators shall validate and import sources through the admin UI.  
**Acceptance Criteria:**
- "Import Sources" page accessible from ImportBatch changelist
- Validate Sources button runs validation and displays results
- Import from directory button runs registered source import
- File upload supports direct Excel upload for registered sources
- ImportBatch record created with operator notes

#### FR-AD-003: QA Reporting
**Priority:** Must-have  
**Description:** The system shall generate QA reports comparing source rows to imported records.  
**Acceptance Criteria:**
- Command `report_repository_qa` generates JSON report
- Report compares validated source counts vs imported counts per dataset
- Reports taxonomy sizes (countries, hazards, NbS types)
- Reports geocoding coverage (% with coordinates)
- Reports missing key fields per dataset
- API endpoint `/repository/qa/` serves latest report

#### FR-AD-004: Health Endpoint
**Priority:** Must-have  
**Description:** The system shall expose a health check endpoint.  
**Acceptance Criteria:**
- `/health/` returns HTTP 200 with basic status
- Used by load balancers and monitoring

---

## 5. User Stories

### US-001: Discovery via Landing Page
> **As a** policymaker,  
> **I want** to select my climate hazard, territory type, and governance scale on the home page,  
> **So that** I can quickly narrow down to relevant evidence.  

**Acceptance Criteria:**
- Hazard picker shows canonical hazard list
- Territory picker shows scope options (country, region, EU, etc.)
- Scale picker shows governance levels
- Live map updates to show matching records
- "Explore" button transitions to Search tab with pre-applied filters

### US-002: Systematic Search
> **As a** researcher,  
> **I want** to search with keywords and apply multiple filters,  
> **So that** I can find all relevant studies on a specific topic.  

**Acceptance Criteria:**
- Free-text search returns results within 2 seconds
- Filters applied without page reload
- Result count updates immediately
- Pagination or infinite scroll for large result sets

### US-003: Map-Based Exploration
> **As a** practitioner,  
> **I want** to see where NbS projects are implemented on a map,  
> **So that** I can find cases near my region.  

**Acceptance Criteria:**
- Map loads within 3 seconds
- Pins cluster when zoomed out
- Clicking a region filters to that geography
- Choropleth shows evidence density by country

### US-004: Gap Identification
> **As a** EU project officer,  
> **I want** to see which NbS–hazard combinations lack evidence,  
> **So that** I can prioritize funding calls.  

**Acceptance Criteria:**
- Gap matrix computed live
- Red highlighting for gaps (<3 records)
- Priority list sortable by deficit size
- Exportable gap report

### US-005: AI-Powered Q&A
> **As a** municipal planner,  
> **I want** to ask "What are the barriers to urban greening in Mediterranean cities?",  
> **So that** I get a synthesized answer with source citations.  

**Acceptance Criteria:**
- Question accepted in natural language
- Relevant records retrieved from OpenSearch
- Answer synthesized by LLM with citations
- Sources clickable to full records
- Response within 30 seconds

### US-006: Policy Comparison
> **As a** policy advisor,  
> **I want** to compare binding vs non-binding policies on coastal NbS across EU member states,  
> **So that** I can benchmark regulatory approaches.  

**Acceptance Criteria:**
- Policy explorer filters by bindingness, country, NbS type, hazard
- Results exportable to CSV
- Side-by-side comparison of selected policies

### US-007: Shortlist for Reporting
> **As a** consultant,  
> **I want** to save interesting records to a shortlist and generate a briefing,  
> **So that** I can include evidence in my client report.  

**Acceptance Criteria:**
- Shortlist persists across tab switches
- Briefing generated as printable HTML
- Briefing includes all record details and source URLs

### US-008: Data Import by Operator
> **As a** data operator,  
> **I want** to import a new batch of Excel files with validation and QA,  
> **So that** the repository stays current with minimal errors.  

**Acceptance Criteria:**
- Validation catches schema mismatches before import
- Import preserves raw data and normalizes taxonomies
- QA report confirms row counts and flags issues
- Reindexing updates search within minutes

---

## 6. Data Requirements

### 6.1 Source Data Schema

The unified `RepositoryRecord` schema supports ~60 fields. Key field categories:

| Category | Fields | Description |
|----------|--------|-------------|
| **Identity** | `source_dataset`, `source_uid`, `source_record_id`, `title` | Core identification |
| **Bibliographic** | `authors`, `publication_year`, `doi`, `source_url` | Citation metadata |
| **Geography** | `country_display`, `city_location`, `latitude`, `longitude`, `geographic_scope` | Location data |
| **Taxonomy** | `primary_hazards`, `secondary_hazards`, `primary_nbs_types`, `secondary_nbs_types` | Classification |
| **Content** | `abstract`, `summary`, `description`, `objective`, `methods` | Textual content |
| **Outcomes** | `outcomes_targeted`, `ecological_impacts`, `socio_economic_impacts` | Results |
| **Implementation** | `implementation_stage`, `implementation_steps`, `barriers`, `enablers`, `lessons` | Practice insights |
| **Governance** | `policy_level`, `governance_insights`, `enforcement_mechanisms` | Policy metadata |
| **Finance** | `funding_source`, `funding_contribution`, `finance_insights` | Economic data |
| **System** | `raw_payload`, `normalized_payload`, `import_batch` | Internal tracking |

### 6.2 Taxonomy Requirements

| Taxonomy | Canonical Values | Source |
|----------|-----------------|--------|
| **Hazards** | Flooding, Wildfires, Drought, Urban Heat, Coastal Erosion, Landslides, Storms, etc. | Normalized from source text |
| **NbS Types** | Green infrastructure, Blue infrastructure, Forest restoration, Wetland restoration, etc. | Normalized from source text |
| **Countries** | EU member states + EFTA + select neighbors | Normalized from source text |

### 6.3 Data Quality Rules

- Every record must have a stable `source_uid`
- Duplicated `source_record_id` values are allowed but create separate records
- Geography must not be forced into country taxonomy if supranational/regional
- Taxonomy normalization must be idempotent
- Raw payload preserved for audit and reprocessing

---

## 7. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-001 | Performance | Search query response time | < 2 seconds |
| NFR-002 | Performance | Bootstrap API response time | < 5 seconds (cached) |
| NFR-003 | Performance | Map initial load time | < 3 seconds |
| NFR-004 | Availability | Uptime (production) | 99.5% |
| NFR-005 | Scalability | Support concurrent users | 50+ simultaneous |
| NFR-006 | Security | No sensitive data in logs | All PII masked |
| NFR-007 | Security | API key storage (AI) | Client-side only, never server-persisted |
| NFR-008 | Maintainability | Dockerized deployment | Single-command startup |
| NFR-009 | Maintainability | Environment-driven config | No secrets in code |
| NFR-010 | Portability | Local dev ports | 9500–9599 range |

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **Bindingness** | Legal force of a policy instrument (binding, non-binding, mixed) |
| **Bootstrap API** | Endpoint that loads full dataset into frontend for client-side operation |
| **Canonical taxonomy** | Standardized, controlled vocabulary for classification |
| **Choropleth** | Thematic map using color to represent statistical values |
| **Evidence gap** | An NbS–hazard combination with insufficient research coverage |
| **M2M** | Many-to-Many database relationship |
| **Normalizer** | Logic that transforms raw source values into canonical forms |
| **Raw payload** | Complete original Excel row preserved as JSON |
| **SourceSpec** | Data class defining schema contract for an Excel source |
| **Source UID** | Stable unique identifier: `dataset:sheet:row_number` |

---

**Document Owner:** Project Lead  
**Review Cycle:** Per release  
**Next Review:** v2 planning phase
