# NbS ReAdapt — Deployment & Operations Guide

**Version:** 1.0  
**Date:** 2026-05-11  
**Audience:** DevOps engineers, system administrators, data operators  
**Status:** Production-ready (first-pass deployment)

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Local Development Deployment](#2-local-development-deployment)
3. [Production Deployment](#3-production-deployment)
4. [Data Pipeline Operations](#4-data-pipeline-operations)
5. [Monitoring & Health Checks](#5-monitoring--health-checks)
6. [Backup & Recovery](#6-backup--recovery)
7. [Troubleshooting](#7-troubleshooting)
8. [Security Hardening](#8-security-hardening)
9. [Maintenance Tasks](#9-maintenance-tasks)

---

## 1. Environment Setup

### 1.1 Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24.x+ | Container runtime |
| Docker Compose | 2.x+ | Stack orchestration |
| Git | 2.x+ | Source control |
| Bash | 4.x+ | Script execution |

### 1.2 Environment File

Copy the sample environment file and customize:

```bash
cp .env.sample .env
```

**Critical variables to set:**

```bash
# Application
APP_SECRET_KEY=<generate-a-strong-secret>
APP_DEBUG=false                    # Set false for production
APP_PORT=9500
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com

# Database
POSTGRES_DB=nbs_readapt
POSTGRES_USER=nbs_readapt
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_PUBLIC_PORT=9501

# OpenSearch
OPENSEARCH_URL=http://opensearch:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=<strong-os-password>
OPENSEARCH_INITIAL_ADMIN_PASSWORD=<strong-os-admin-password>
OPENSEARCH_INDEX_BM25=nbs_repository_bm25

# AI (if using assistant)
ASSISTANT_PROVIDER=vllm
RUNPOD_VLLM_HOST=https://your-runpod-endpoint.runpod.net
VLLM_API_KEY=<your-api-key>
VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# Or use Anthropic instead of VLLM
# ASSISTANT_PROVIDER=anthropic
# ANTHROPIC_API_KEY=<your-api-key>
# ANTHROPIC_MODEL=claude-3-5-haiku-latest

# Deployment
APP_DOMAIN=nbs-readapt.example.com
LETSENCRYPT_EMAIL=admin@example.com
TRAEFIK_DASHBOARD_HOST=traefik-nbs-readapt.example.com
TRAEFIK_DASHBOARD_CREDENTIALS=admin:<htpasswd-hash>
```

**Generate a Django secret key:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Generate an htpasswd hash for Traefik dashboard:**

```bash
# Install apache2-utils if needed
htpasswd -nb admin your-password | sed 's/\$/$$/g'
```

---

## 2. Local Development Deployment

### 2.1 Full Startup

```bash
# Build and start all services
docker compose up --build -d

# Or use the helper script
bash scripts/rebuild.sh
```

### 2.2 Initialize the Database

```bash
# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### 2.3 Load Initial Data

```bash
# Validate sources
docker compose exec web python manage.py validate_repository_sources

# Import the numbered bundle
docker compose exec web python manage.py import_initial_input --reset

# Build search index
docker compose exec web python manage.py index_repository_records --recreate

# Generate QA report
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
```

### 2.4 Access Points (Local)

| Service | URL | Credentials |
|---------|-----|-------------|
| Web App | http://localhost:9500/ | — |
| Django Admin | http://localhost:9500/admin/ | superuser |
| Health Check | http://localhost:9500/health/ | — |
| pgAdmin | http://localhost:9502/ | `.env` values |
| OpenSearch | http://localhost:9503/ | `.env` values |

### 2.5 Daily Development Commands

```bash
# Start without rebuilding (code changes only)
bash scripts/up.sh

# Rebuild images (Dockerfile/requirements changed)
bash scripts/rebuild.sh

# Full data refresh (import logic changed)
bash scripts/refresh_repository_data.sh

# View logs
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f opensearch

# Django shell
docker compose exec web python manage.py shell

# Run checks
docker compose exec web python manage.py check
```

### 2.6 Stopping the Stack

```bash
# Stop containers
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v
```

---

## 3. Production Deployment

### 3.1 Architecture

Production uses a **two-stack model** for separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│  Stack 1: Traefik Reverse Proxy                         │
│  - Ports 80/443 exposed                                 │
│  - Let's Encrypt TLS                                    │
│  - Shared network: nbs_readapt_proxy                    │
├─────────────────────────────────────────────────────────┤
│  Stack 2: Application                                   │
│  - Web (Django)                                         │
│  - PostgreSQL                                           │
│  - OpenSearch                                           │
│  - Joins proxy network for routing                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Deploy Traefik Stack

```bash
cd deploy/traefik/

# Create shared network
docker network create nbs_readapt_proxy 2>/dev/null || true

# Start Traefik
docker compose up -d
```

Verify Traefik is running:

```bash
curl http://localhost:8080/api/rawdata  # Dashboard API
curl http://localhost                   # Should redirect to HTTPS
```

### 3.3 Deploy Application Stack

```bash
cd deploy/app/

# Pull latest image
docker compose pull

# Start app
docker compose up -d
```

### 3.4 Initialize Production Database

```bash
# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Import data (same commands as local)
docker compose exec web python manage.py import_initial_input --reset
docker compose exec web python manage.py index_repository_records --recreate
```

### 3.5 Build and Push Image

```bash
# Build production image
bash build_and_push_images.sh
```

This script:
1. Builds `ghcr.io/pranavnbapat/nbs_readapt:latest`
2. Pushes to GitHub Container Registry

### 3.6 Traefik Labels (in `deploy/app/docker-compose.yml`)

```yaml
services:
  web:
    image: ghcr.io/pranavnbapat/nbs_readapt:latest
    networks:
      - default
      - nbs_readapt_proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nbs_readapt.rule=Host(`${APP_DOMAIN}`)"
      - "traefik.http.routers.nbs_readapt.entrypoints=websecure"
      - "traefik.http.routers.nbs_readapt.tls.certresolver=letsencrypt"
      - "traefik.http.services.nbs_readapt.loadbalancer.server.port=8000"
```

### 3.7 Production Checklist

- [ ] `.env` configured with strong passwords
- [ ] `APP_DEBUG=false`
- [ ] `ALLOWED_HOSTS` set to production domain
- [ ] `CSRF_TRUSTED_ORIGINS` includes HTTPS domain
- [ ] SSL certificates auto-provisioned via Let's Encrypt
- [ ] Database migrations applied
- [ ] Initial data imported and indexed
- [ ] Superuser created
- [ ] Health endpoint responding
- [ ] Traefik dashboard protected with basic auth
- [ ] Firewall rules set (ports 80, 443 open; others restricted)

---

## 4. Data Pipeline Operations

### 4.1 Pipeline Overview

```
Excel Sources → Validate → Import → PostgreSQL → Reindex → OpenSearch → QA
```

### 4.2 Standard Operating Procedure: Full Refresh

```bash
# 1. Validate all sources
docker compose exec web python manage.py validate_repository_sources

# 2. Import with reset
docker compose exec web python manage.py import_initial_input --reset

# 3. Rebuild search index
docker compose exec web python manage.py index_repository_records --recreate

# 4. Generate QA report
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
```

Or use the one-shot script:

```bash
bash scripts/refresh_repository_data.sh
```

### 4.3 Selective Import

Import only specific datasets:

```bash
docker compose exec web python manage.py import_repository_sources --dataset papers --dataset policies
```

Import a specific file:

```bash
docker compose exec web python manage.py import_repository_sources --filename 04_Policies.xlsx
```

### 4.4 Validation Only

```bash
# All sources
docker compose exec web python manage.py validate_repository_sources

# Specific dataset
docker compose exec web python manage.py validate_repository_sources --dataset papers

# Specific file
docker compose exec web python manage.py validate_repository_sources --filename 04_Policies.xlsx
```

### 4.5 Adding a New Excel Source

#### Case A: Matches Existing Schema

1. Place file in `initial_input/`
2. Register in `apps/repository/source_specs.py` if filename differs
3. Validate
4. Import
5. Reindex
6. QA

#### Case B: New Schema

1. Inspect workbook structure
2. Add new `SourceSpec` to `source_specs.py`
3. Extend normalizer in `services.py`
4. Validate
5. Import
6. Reindex
7. QA

### 4.6 Reindexing Rules

| Scenario | Action Required |
|----------|----------------|
| New data imported | Reindex |
| Record edited in PostgreSQL | Reindex |
| Search document shape changed | Reindex + possibly re-import |
| Taxonomy normalized differently | Re-import + reindex |
| OpenSearch container restarted | No action (data persists in volume) |

**Safe reindex command:**

```bash
docker compose exec web python manage.py index_repository_records --recreate
```

### 4.7 Document Preparation (Inspection)

Export OpenSearch-ready JSONL for inspection:

```bash
docker compose exec web python manage.py prepare_search_documents
docker compose exec web python manage.py prepare_search_documents --dataset papers --limit 25
```

Output: `data/exports/opensearch_repository_documents.jsonl`

---

## 5. Monitoring & Health Checks

### 5.1 Health Endpoint

```bash
curl -f http://localhost:9500/health/ || echo "UNHEALTHY"
```

Use this for load balancer health checks and uptime monitoring.

### 5.2 Container Status

```bash
docker compose ps
docker compose stats
```

### 5.3 Log Inspection

```bash
# Web application logs
docker compose logs -f web --tail=100

# Database logs
docker compose logs -f postgres --tail=50

# OpenSearch logs
docker compose logs -f opensearch --tail=50
```

### 5.4 OpenSearch Cluster Health

```bash
curl -sS http://localhost:9503/_cluster/health | python -m json.tool
```

Expected status: `yellow` (single-node) or `green` (multi-node).

### 5.5 Index Stats

```bash
curl -sS http://localhost:9503/_cat/indices?v
curl -sS http://localhost:9503/nbs_repository_bm25/_stats | python -m json.tool
```

### 5.6 Database Connection Test

```bash
docker compose exec postgres psql -U nbs_readapt -d nbs_readapt -c "SELECT COUNT(*) FROM repository_repositoryrecord;"
```

---

## 6. Backup & Recovery

### 6.1 PostgreSQL Backup

```bash
# Full database dump
docker compose exec postgres pg_dump -U nbs_readapt nbs_readapt > backups/nbs_readapt_$(date +%Y%m%d_%H%M%S).sql

# Compressed
docker compose exec postgres pg_dump -U nbs_readapt nbs_readapt | gzip > backups/nbs_readapt_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 6.2 PostgreSQL Restore

```bash
# Drop and recreate database (caution!)
docker compose exec postgres psql -U nbs_readapt -c "DROP DATABASE nbs_readapt;"
docker compose exec postgres psql -U nbs_readapt -c "CREATE DATABASE nbs_readapt;"

# Restore from dump
docker compose exec -T postgres psql -U nbs_readapt -d nbs_readapt < backups/nbs_readapt_20260511_120000.sql
```

### 6.3 OpenSearch Backup (Snapshot)

OpenSearch data is derived from PostgreSQL. In most cases, reindexing is sufficient. For large indices, configure snapshot repositories:

```bash
# Register FS snapshot repo
curl -X PUT "localhost:9503/_snapshot/backup_repo" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fs",
    "settings": {"location": "/usr/share/opensearch/snapshots"}
  }'

# Create snapshot
curl -X PUT "localhost:9503/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)"
```

### 6.4 Source File Backup

Keep the `initial_input/` directory under version control or backup:

```bash
# Tar backup
tar czf backups/initial_input_$(date +%Y%m%d).tar.gz initial_input/
```

### 6.5 Full Recovery Procedure

1. Restore PostgreSQL from latest dump
2. Verify data integrity: `report_repository_qa`
3. Rebuild OpenSearch index: `index_repository_records --recreate`
4. Verify search: `search/query/?q=test`
5. Verify application health: `/health/`

---

## 7. Troubleshooting

### 7.1 Application Won't Start

**Symptom:** `docker compose up` fails or web container exits.

**Checklist:**
- [ ] `.env` file exists and is complete
- [ ] Required ports not in use: `lsof -i :9500-9504`
- [ ] Docker daemon running: `docker info`
- [ ] Sufficient disk space: `df -h`

### 7.2 OpenSearch Fails to Start

**Symptom:** `opensearch` container exits or loops.

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Missing `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | Set in `.env` (min 8 chars, uppercase, lowercase, digit) |
| Insufficient Docker memory | Increase Docker Desktop memory to 4GB+ |
| Volume corruption | `docker compose down -v` and restart (data loss!) |

**Check OpenSearch logs:**
```bash
docker compose logs opensearch --tail=100
```

### 7.3 Search Returns No Results

**Symptom:** `/search/query/` returns empty hits.

**Checklist:**
1. Check PostgreSQL has records:
   ```bash
   docker compose exec web python manage.py shell -c "from apps.repository.models import RepositoryRecord; print(RepositoryRecord.objects.count())"
   ```
2. Check OpenSearch index exists:
   ```bash
   curl -sS http://localhost:9503/_cat/indices?v
   ```
3. Reindex if missing:
   ```bash
   docker compose exec web python manage.py index_repository_records --recreate
   ```
4. Check OpenSearch health:
   ```bash
   curl -sS http://localhost:9503/_cluster/health
   ```

### 7.4 Import Validation Failures

**Symptom:** `validate_repository_sources` reports errors.

**Common issues:**
- File not in `initial_input/`
- Wrong worksheet name (check `source_specs.py`)
- Missing required columns
- Duplicate `source_record_id` values

**Fix:**
1. Verify file location and name
2. Open Excel and confirm sheet names and column headers
3. Update `source_specs.py` if schema changed
4. Re-run validation

### 7.5 AI Assistant Errors

**Symptom:** `/assistant/chat/` returns 502 or error.

**Checklist:**
- [ ] `RUNPOD_VLLM_HOST` or `VLLM_CHAT_COMPLETIONS_URL` configured
- [ ] `VLLM_API_KEY` valid and not expired
- [ ] `VLLM_MODEL` specified
- [ ] LLM endpoint reachable from web container:
  ```bash
  docker compose exec web curl -I $RUNPOD_VLLM_HOST
  ```
- [ ] Assistant timeout not exceeded (default 120s)

### 7.6 pgAdmin Connection Issues

**Symptom:** pgAdmin cannot connect to database.

**Fix:** In pgAdmin server registration, use:
- Host: `postgres` (not `localhost` — it's inside Docker network)
- Port: `5432`

### 7.7 Slow Performance

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Slow page load | Bootstrap API not cached | Wait for cache; check `ALL_RECS` size |
| Slow search | OpenSearch under-resourced | Allocate more memory to OS container |
| Slow import | Row-by-row processing | Expected for large files; batch size adjustable |
| Slow map | Too many pins | Filter before viewing map |

---

## 8. Security Hardening

### 8.1 Current Security Posture

| Layer | Status | Notes |
|-------|--------|-------|
| TLS | ✅ Traefik + Let's Encrypt | Auto-provisioned |
| HTTPS redirect | ✅ Traefik middleware | Forces HTTPS |
| HSTS | ✅ Traefik middleware | HTTP Strict Transport Security |
| Django debug | ⚠️ Env-controlled | Must be `false` in production |
| OpenSearch security | ⚠️ Disabled in dev | Must enable in production |
| Static files | ⚠️ Django dev server | Should use WhiteNoise or CDN |
| WSGI server | ⚠️ Django runserver | Should use Gunicorn |
| Rate limiting | ❌ Not implemented | Add Traefik or Django rate limiting |

### 8.2 Recommended Hardening Steps

1. **Replace runserver with Gunicorn**
   ```dockerfile
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "config.wsgi:application"]
   ```

2. **Serve static files with WhiteNoise**
   ```bash
   pip install whitenoise
   # Add to MIDDLEWARE above SecurityMiddleware
   ```

3. **Enable OpenSearch security plugin in production**
   - Remove `plugins.security.disabled=true`
   - Configure certificates and roles

4. **Add rate limiting**
   - Traefik: `middlewares.rateLimit`
   - Django: `django-ratelimit`

5. **Set security headers**
   ```python
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   X_FRAME_OPTIONS = "DENY"
   ```

6. **Rotate secrets regularly**
   - `APP_SECRET_KEY`
   - Database passwords
   - OpenSearch passwords
   - VLLM API keys

---

## 9. Maintenance Tasks

### 9.1 Daily

- Check container status: `docker compose ps`
- Review error logs: `docker compose logs web --tail=50`
- Verify health endpoint: `curl /health/`

### 9.2 Weekly

- Review disk usage: `df -h` and `docker system df`
- Check OpenSearch cluster health
- Review QA report for anomalies

### 9.3 Monthly

- Backup PostgreSQL database
- Backup source files (`initial_input/`)
- Review and rotate secrets
- Update base images (`docker compose pull`)
- Check for security advisories (Django, OpenSearch, PostgreSQL)

### 9.4 On-Demand

- Reindex OpenSearch after data changes
- Run full QA after bulk imports
- Scale resources if performance degrades
- Purge old Docker images and volumes: `docker system prune -a`

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start stack | `bash scripts/up.sh` |
| Rebuild stack | `bash scripts/rebuild.sh` |
| Full data refresh | `bash scripts/refresh_repository_data.sh` |
| Validate sources | `docker compose exec web python manage.py validate_repository_sources` |
| Import bundle | `docker compose exec web python manage.py import_initial_input --reset` |
| Reindex search | `docker compose exec web python manage.py index_repository_records --recreate` |
| QA report | `docker compose exec web python manage.py report_repository_qa` |
| Django shell | `docker compose exec web python manage.py shell` |
| Create superuser | `docker compose exec web python manage.py createsuperuser` |
| DB backup | `docker compose exec postgres pg_dump -U nbs_readapt nbs_readapt > backup.sql` |
| Health check | `curl http://localhost:9500/health/` |
| OS indices | `curl http://localhost:9503/_cat/indices?v` |

---

**Document Owner:** DevOps Lead  
**Review Cycle:** Per deployment  
**Last Updated:** 2026-05-11
