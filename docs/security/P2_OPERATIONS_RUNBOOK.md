# P2 Operations and Recovery Runbook

Tracks #40, #42, #43 and #44 in epic #16.

## Local clean-clone validation
From a new checkout with Docker Compose v2, Node 22 and Python 3.12:

1. Copy `.env.example` to `.env`.
2. Replace all sample passwords with different, long random credentials; never commit `.env`.
3. Run `docker compose config --quiet` and `docker compose up --build -d`.
4. Check `http://127.0.0.1:8000/health/ready` for an OK database and `http://127.0.0.1:3000/` for UI.
5. Run `PYTHONPATH=services/api:. INVESTHELPER_ENV=test INVESTHELPER_DATABASE_URL=sqlite:///./test-investhelper-p0.db python -m pytest services/api/tests`.
6. Stop with `docker compose down` (without `-v` to preserve your local data).

CI reproduces those steps from a clean checkout in `p2-compose-recovery.yml`.

## Structured logs
The API records bounded `http.request` JSON events: generated request ID,
route **template**, HTTP method/status and duration. The worker logs
`ingestion.succeeded` and `ingestion.failed` with provider, issuer ID,
job ID, attempts, data counts and exception **type** only.

Never log bearer tokens, passwords, database URLs, full query strings,
raw source documents, personal identifiers or provider credentials.
Logs are not a substitute for tracing a future valuation run;
that remains dependent on an actual valuation engine.

## Database backup and recovery
The CI recovery job creates a `pg_dump -Fc` archive and restores it into
a **different** database using `pg_restore`; it verifies that migration
history and public tables were restored. CI never uses real credentials.

For production, enable automated provider-managed PostgreSQL backups and
point-in-time recovery, retain encrypted offsite backups, and schedule
an isolated restore rehearsal. A safe initial **target**, subject to your
hosting and data criticality, is RPO 24 hours and RTO 4 hours. These are
**targets, not achieved recovery guarantees**.

When the data is live:
- Restore in a separate environment, never on top of the primary DB.
- Validate schema, row counts, provider evidence references, migration
  history, job-queue state, and application read-only readiness.
- Reconcile `SourceSnapshot.object_key` entries against the object store.
- Protect backups with restricted service credentials and encrypted storage;
  test deletion/restore of one immutably-addressed sample blob.
- Document a retention policy, actual restore duration, owner and date.

## Object storage
The existing P1 MinIO acceptance CI checks conditional immutable writes
and content-hash integrity against a real S3-compatible container.
This does **not** prove a real production backup was scheduled or restored.
Do not close #43 until you have configured storage backups/replication and
performed an independent restore with the selected hosting provider.

## Open manual actions
- #36: production private networking, service-level TLS and access controls.
- #37: register an OIDC issuer/client and set signed token audience + HTTPS JWKS
  URL. Backend ownership enforcement is implemented and offline-tested.
- #38: review actual source license contracts and public redistribution rights.
- #41: require GitHub branch rules/checks and optionally code-owner approval.
- #43: select actual backup retention and verify a hosted restore.
