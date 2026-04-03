# NbS ReAdapt Assessment

This document is historical context. It explains why `nbs_readapt` exists and how it differs from the older `readapt` prototype.

## What the old `readapt` folder is

The earlier `readapt` work is a searchable repository prototype built around:

- a FastAPI app in `readapt/app`
- OpenSearch indexes and ingest scripts in `readapt/scripts`
- one consolidated Excel workbook: `Sample Data for ReAdapt_Database_8_1_2026_standardised.xlsx`

It supports:

- BM25 search (`readapt_v1`)
- neural search (`readapt_v2`)
- hybrid search
- server-side facet filtering

The earlier implementation normalized four sheets from one workbook:

- `EU Funded Project`
- `Platform Case Studies`
- `Paper`
- `Policies`

The field audit in `readapt/reports` shows the first pass of content design:

- ranking fields were chosen per sheet
- facet fields were chosen per sheet
- a single searchable `search_text` field was generated
- the full raw row payload was preserved in `data`

## What the new `nbs_readapt` folder is

The new folder started as source inputs and reference HTML prototypes. It is now the active application stack for this project.

Files in `nbs_readapt/initial_input`:

- `01_Papers_Report.xlsx` with 410 rows
- `02_Network_Projects.xlsx` with 103 rows
- `03_EU Funded_Projects.xlsx` with 275 rows
- `04_Policies.xlsx` with 769 rows
- `Core Concept_Key Terms.xlsx` with 27 rows
- `index.html`
- `index_ai.html`

This is a broader NbS repository than the older prototype. The schema is richer and more explicit around:

- NbS types
- hazards
- territorial context
- governance
- finance
- community engagement
- implementation stage
- outcomes and lessons

Total primary records across the four numbered files: 1,557.

## What `index.html` is doing

`index.html` is a large single-file client-side prototype.

It appears to embed:

- the repository records directly in JavaScript
- analytics and summary structures
- UI logic for search, map, analytics, shortlist, and decision support

So this is not just a page shell. It is already acting as a bundled data application.

## What `index_ai.html` adds

`index_ai.html` is basically `index.html` plus an inline chat experience:

- a new `Ask the Repository` tab
- a browser-side Anthropic API call
- API key input stored in `sessionStorage`
- lightweight local retrieval over the embedded records before sending context to the model

Important implication:

- the current AI prototype is client-side and exposes model access from the browser
- that is acceptable for a private demo, but not the right shape for a production build

## Scope shift

The old scope was:

- ingest one workbook
- create OpenSearch indexes
- provide search endpoints
- render a simple search UI

The new scope is clearly larger:

- a curated NbS knowledge repository
- richer domain model and stronger content taxonomy
- map and analytics views
- decision-support content
- optional AI assistant

This means the new work should not be a small extension of the old UI. It should reuse the good parts of the old pipeline thinking, but the product shape is now closer to a proper repository application.

## What has already been done in `nbs_readapt`

The recommended direction above has already been implemented in principle:

- the HTML files are now treated as references only
- the application runs as a proper Django stack
- PostgreSQL is the source of truth
- OpenSearch is a derived search layer
- the UI is backed by real APIs instead of embedded source data

## Current recommendation

Keep this file as project context only.

For active documentation, use:

- [README.md](/home/pranav/PyCharm/Parveen/nbs_readapt/README.md)
- [OPERATIONS.md](/home/pranav/PyCharm/Parveen/nbs_readapt/OPERATIONS.md)
- [PIPELINE.md](/home/pranav/PyCharm/Parveen/nbs_readapt/PIPELINE.md)
- [ARCHITECTURE.md](/home/pranav/PyCharm/Parveen/nbs_readapt/ARCHITECTURE.md)
