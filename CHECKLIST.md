# Delivery Checklist

This checklist tracks what is already in place and what still remains before final handover.

## In place

- Django application scaffold
- Dockerized local stack
- PostgreSQL database
- OpenSearch single-node setup
- pgAdmin
- `.env.sample`
- `.gitignore`
- Dockerfile
- `docker-compose.yml`
- unified repository schema
- Excel source validation workflow
- Excel import workflow
- admin-assisted import screen
- raw payload preservation
- normalized taxonomy handling
- OpenSearch BM25 indexing pipeline
- search query API
- search facets API
- geography-aware filtering
- record detail API
- repository overview API
- repository QA API
- search, map, analytics UI
- markdown handover docs

## Current operator workflows available

- start the stack
- migrate the database
- validate registered source files
- import registered source files
- prepare OpenSearch-ready documents
- index OpenSearch from PostgreSQL
- run QA reporting
- use Django admin for import operations

## Still to do

- server-side AI assistant
- neural search
- hybrid search
- production deployment hardening
- reverse proxy setup for production
- authentication/permissions design if required
- shell automation scripts for installation and handover
- final deployment notes
- explicit treatment of remaining special geography edge cases

## Handover readiness

Current state:

- good for local development and internal handover
- good for operator-driven imports and QA
- not yet production-complete

## Recommended next milestone

Before final handover, complete:

1. shell scripts for setup and common operations
2. deployment-oriented Docker or proxy setup
3. assistant architecture decision
4. final operator runbook validation from a clean machine
