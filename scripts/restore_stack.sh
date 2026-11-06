#!/usr/bin/env bash
# Restore only to a *new* PostgreSQL database and new S3 bucket prefix.
set -euo pipefail
umask 077
: "${BACKUP_FILE:?Path to encrypted age archive}"
: "${BACKUP_AGE_IDENTITY:?Path to age decryption identity}"
: "${RESTORE_DB_NAME:?New database name required}"
: "${RESTORE_BUCKET_PREFIX:?New bucket prefix required}"
: "${MINIO_ROOT_USER:?Required}"
: "${MINIO_ROOT_PASSWORD:?Required}"
[[ "$RESTORE_DB_NAME" =~ ^[a-z][a-z0-9_]{0,49}$ ]] || { echo "Unsafe restore DB name" >&2; exit 2; }
[[ "$RESTORE_BUCKET_PREFIX" =~ ^[a-z][a-z0-9-]{0,19}$ ]] || { echo "Unsafe restore bucket prefix" >&2; exit 2; }
command -v age >/dev/null
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
age -d -i "$BACKUP_AGE_IDENTITY" "$BACKUP_FILE" | tar -C "$temp" -xf -
(cd "$temp" && sha256sum -c SHA256SUMS)
exists="$(docker compose exec -T db psql -U "${POSTGRES_USER:-investhelper}" -d postgres -Atc \
  "select count(*) from pg_database where datname='$RESTORE_DB_NAME'")"
[[ "$exists" == "0" ]] || { echo "Refusing to overwrite existing database" >&2; exit 3; }
docker compose exec -T db createdb -U "${POSTGRES_USER:-investhelper}" "$RESTORE_DB_NAME"
docker compose exec -T db pg_restore --no-owner --no-acl -U "${POSTGRES_USER:-investhelper}" \
  -d "$RESTORE_DB_NAME" < "$temp/postgres.dump"
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api \
  python scripts/object_store_archive.py restore --prefix "$RESTORE_BUCKET_PREFIX" < "$temp/minio.tar"
echo "Restored new database $RESTORE_DB_NAME and new object-store bucket prefix $RESTORE_BUCKET_PREFIX"
