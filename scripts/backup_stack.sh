#!/usr/bin/env bash
# Operator-triggered encrypted backup; schedule and retention are deployment responsibilities.
set -euo pipefail
umask 077
: "${POSTGRES_PASSWORD:?Required}"
: "${MINIO_ROOT_USER:?Required}"
: "${MINIO_ROOT_PASSWORD:?Required}"
: "${BACKUP_AGE_RECIPIENT:?An age public recipient is required}"
: "${BACKUP_DIRECTORY:?Set absolute backup destination outside Compose volumes}"
command -v age >/dev/null
command -v sha256sum >/dev/null
mkdir -p "$BACKUP_DIRECTORY"
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$BACKUP_DIRECTORY/popudo-${stamp}-$$.tar.age"
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-investhelper}" \
  -d "${POSTGRES_DB:-investhelper}" -Fc > "$temp/postgres.dump"
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api \
  python scripts/object_store_archive.py backup > "$temp/minio.tar"
(cd "$temp" && sha256sum postgres.dump minio.tar > SHA256SUMS)
tar -C "$temp" -cf - postgres.dump minio.tar SHA256SUMS |
  age -r "$BACKUP_AGE_RECIPIENT" -o "$output"
test -s "$output"
echo "Encrypted backup written: $output"
