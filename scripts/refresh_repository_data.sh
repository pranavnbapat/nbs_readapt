#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose exec web python manage.py migrate
docker compose exec web python manage.py sync_repository_sources --reset
docker compose exec web python manage.py report_repository_qa --output data/exports/repository_qa_report.json
