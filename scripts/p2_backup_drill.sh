#!/usr/bin/env bash
# Isolated PostgreSQL + S3 backup/recovery acceptance. Never touches the default Compose project.
set -euo pipefail
export COMPOSE_PROJECT_NAME="p2drill${GITHUB_RUN_ID:-$$}"
: "${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD for the drill}"
: "${MINIO_ROOT_USER:?Set MINIO_ROOT_USER for the drill}"
: "${MINIO_ROOT_PASSWORD:?Set MINIO_ROOT_PASSWORD for the drill}"
workspace="$(mktemp -d)"
cleanup() {
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$workspace"
}
trap cleanup EXIT
docker compose up --build -d --wait --wait-timeout 240 db minio api
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api python - <<'PY'
import boto3, os, time
for attempt in range(30):
    try:
        s3 = boto3.client("s3", endpoint_url="http://minio:9000",
                          aws_access_key_id=os.environ["MINIO_ROOT_USER"],
                          aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
                          region_name="us-east-1")
        s3.create_bucket(Bucket="popudo-drill-source")
        s3.put_object(Bucket="popudo-drill-source", Key="evidence/document.bin",
                      Body=b"popudo-recovery-fixture", ContentType="application/octet-stream")
        break
    except Exception:
        if attempt == 29:
            raise
        time.sleep(2)
PY
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-investhelper}" \
  -d "${POSTGRES_DB:-investhelper}" -Fc > "$workspace/postgres.dump"
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api \
  python scripts/object_store_archive.py backup > "$workspace/minio.tar"
test -s "$workspace/postgres.dump"
test -s "$workspace/minio.tar"
(cd "$workspace" && sha256sum postgres.dump minio.tar > SHA256SUMS && sha256sum -c SHA256SUMS)
docker compose exec -T db createdb -U "${POSTGRES_USER:-investhelper}" p2_recovery_verification
docker compose exec -T db pg_restore --no-owner --no-acl -U "${POSTGRES_USER:-investhelper}" \
  -d p2_recovery_verification < "$workspace/postgres.dump"
table_count="$(docker compose exec -T db psql -U "${POSTGRES_USER:-investhelper}" \
  -d p2_recovery_verification -Atc "select count(*) from information_schema.tables where table_schema='public'")"
test "$table_count" -gt 0
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api \
  python scripts/object_store_archive.py restore --prefix restored- < "$workspace/minio.tar"
docker compose exec -T -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD api python - <<'PY'
import boto3, os
s3 = boto3.client("s3", endpoint_url="http://minio:9000",
                   aws_access_key_id=os.environ["MINIO_ROOT_USER"],
                   aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
                   region_name="us-east-1")
old = s3.get_object(Bucket="popudo-drill-source", Key="evidence/document.bin")["Body"].read()
new = s3.get_object(Bucket="restored-popudo-drill-source", Key="evidence/document.bin")["Body"].read()
assert old == new == b"popudo-recovery-fixture"
PY
echo "P2 PostgreSQL and MinIO backup -> independent restore passed"
