#!/usr/bin/env bash
# Run from the repository root after setting .env.
set -euo pipefail
test -f .env || { echo "Missing .env: copy .env.staging.example and set secrets" >&2; exit 2; }
mode="$(stat -c '%a' .env)"
case "$mode" in 600|400) ;; *) echo ".env permissions must be 600 or 400 (currently $mode)" >&2; exit 2 ;; esac
export COMPOSE_PROJECT_NAME=popudo-staging
docker compose -f docker-compose.yml -f compose.staging.yaml config --format json |
  python3 scripts/staging/check_config.py
docker compose -f docker-compose.yml -f compose.staging.yaml up -d --build
bash scripts/staging/smoke.sh
docker compose -f docker-compose.yml -f compose.staging.yaml ps
