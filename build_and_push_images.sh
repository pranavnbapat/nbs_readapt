#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

DEFAULT_IMAGE="ghcr.io/pranavnbapat/espon_readapt:latest"
IMAGE_TAG="${1:-${APP_IMAGE:-${DEFAULT_IMAGE}}}"

echo "Project root: ${PROJECT_ROOT}"
echo "Target image: ${IMAGE_TAG}"

cd "${PROJECT_ROOT}"

APP_IMAGE="${IMAGE_TAG}" docker compose build web
APP_IMAGE="${IMAGE_TAG}" docker compose push web

echo "Build and push completed for ${IMAGE_TAG}"
