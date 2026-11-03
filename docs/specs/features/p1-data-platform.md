# P1 — Verifiable Financial Data Platform

**Epic:** #16 | **Issues:** #19, #21, #22, #24–#34  
**Status:** Implementation branch `feat/p1-data-platform` (PR #59).

## Goals and non-goals
- Preserve source identity and immutable raw data, with reproducible normalized facts.
- Support distinct issuers, securities, share classes, ADRs and exchange-scoped historical symbols.
- Make ingestion retryable, rate-limited, idempotent and independent from HTTP routes.
- Never publish a financial ratio, stock score or price target without complete inputs.
- This phase **does not** implement investment strategies, valuations, backtesting or accounts.
- A US SEC adapter is included; European financial statements and market prices
  require a licensed provider/official source and credentials. No fabricated fallback exists.

## Architecture

```mermaid
flowchart TD
  Cron[External scheduler] --> Job[DB ingestion_job queue]
  Job --> Worker[Explicit ingestion CLI worker]
  Worker --> Identity[Verified issuer / CIK mapping]
  Identity --> Provider[Provider adapter]
  Provider --> Snapshot[Content-addressed immutable S3 / MinIO snapshot]
  Snapshot --> Normalize[Domain normalization + provenance checks]
  Normalize --> Facts[(PostgreSQL financial_fact / quotes / FX)]
  Facts --> Query[Time-aware research query]
  Query --> API[FastAPI bounded APIs]
  API --> Web[Next.js frontend]
```

Provider protocol: `services/api/app/modules/ingestion/contracts.py`  
SEC adapter: `providers.py`  
Importer: `pipeline.py`  
Job queue: `jobs.py`  
Storage: `storage.py`  
Accounting: `normalization.py`, `calculations.py`  
Identity: `identity.py`

## Data and reliability rules

1. A `company` is an **issuer**. Display tickers are NOT unique. `security`
   identifies share class/ISIN; `security_listing` scopes symbols by MIC
   and effective dates, with aliases captured separately.
2. Trusted external IDs (e.g. SEC CIK) require independent attestation against
   an official provider before queueing jobs.
3. Source payloads are SHA-256 content addressed. New filings/restatements
   are preserved rather than overwriting previous source versions.
4. All numeric accounting values are Decimal, with explicit original unit and
   currency; no implicit FX, unit guess, or YTD-as-quarter conversion.
5. `financial_fact` and `quote_observation` have provider/version natural
   keys. Re-importing the same evidence is idempotent; conflicting values
   for one filing/revision fail closed.
6. A point-in-time query excludes facts reported or collected **after**
   its `as_of` date. The caller can reconstruct evidence available then.
7. Ingestion work never executes on web request threads; workers use
   bounded exponential retry, rate limits, expired leases and dead-letter states.
8. Application import does not create tables or seed data. Database schema
   changes run via `scripts/migrate.py` in a transaction with checksum checks
   and a PostgreSQL advisory lock.

## Migration and startup

Use **PostgreSQL 16**. Back up existing DB first. From repository root:

```bash
export PYTHONPATH=services/api:.
export INVESTHELPER_DATABASE_URL='postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB'
python scripts/migrate.py
python scripts/migrate.py  # idempotence
python scripts/check_schema.py
uvicorn app.main:app --app-dir services/api
```

Docker Compose API starts with an explicit migration command and waits for
the DB readiness check. A pre-migration API returns HTTP 503 from
`/health/ready`, while `/health/live` tests process liveness only.

## How to ingest SEC data

US XBRL data require no paid data key, but SEC requires a descriptive
`User-Agent` with an email/contact. Identify an existing company record
and its official SEC CIK, and set:

```bash
export INVESTHELPER_SEC_USER_AGENT='Popudo Research contact@example.com'
export INVESTHELPER_S3_BUCKET='investhelper-source-snapshots'
export INVESTHELPER_S3_ENDPOINT='http://minio:9000'
# Provide appropriate AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY via secrets.
```

Create the bucket beforehand; avoid public bucket access. For **local
development only**, omit S3 settings and set
`INVESTHELPER_ENV=development`, storing snapshots in `./data/snapshots`.

```bash
python scripts/initialize_taxonomy.py
python scripts/register_company.py --name 'NVIDIA Corporation' --ticker NVDA --exchange NASDAQ --country USA --sector Semiconductors --industry Semiconductors --currency USD
# Use the ID printed by the previous command; 2 is only illustrative.
python scripts/link_sec_company.py --company-id 2 --cik 0001045810
python scripts/enqueue_ingestion.py --company-id 2 --provider sec_edgar --subject 0001045810
python scripts/run_ingestion_jobs.py --once
python scripts/ingestion_status.py
```

The example company ID is illustrative; always use the ID returned by registration. Production onboarding never inserts financial fixtures or generates ISINs.
The identity linking command checks the SEC CIK and reported ticker, refusing
mismatched issuers. A scheduler can invoke
`scripts/schedule_verified_ingestion.py` (idempotent) followed by worker
processes. For rate limits, a 429 triggers an explicit bounded backoff.

## API contract

- `GET /health/live`: process readiness only.
- `GET /health/ready`: verifies DB connection and required schema; 503 on failure.
- `GET /api/companies/page?limit=50&offset=0&q=...&country_id=...&sector_id=...`:
  deterministic, typed page with total count.
- `GET /api/companies/{id}/facts?as_of=2026-11-03T00:00:00Z`:
  only raw-source-backed facts published and retrieved by that time.
- `GET /api/companies/{id}/listings`: verified listing identities.
- `GET /api/companies/{id}/quotes`: source-backed quotes or typed missing/stale errors.
- Legacy company list/search endpoints remain list-shaped but are capped at 100 rows.

Money fields are JSON decimal strings to preserve precision, not JS
floating-point numbers. Frontend consumers must parse/format them consciously.

## Testing

```bash
PYTHONPATH=services/api:. python -m pytest -q services/api/tests
```

GitHub Actions `p1-data-platform.yml` also runs the versioned migrations
twice on PostgreSQL 16 and checks all mapped schema columns, constraints
and indexes. Offline SEC fixtures validate that quarterly YTD observations
are not mislabeled as standalone quarters.

## Remaining provider-dependent requirements

This branch establishes the adapter boundaries and one real US filings
provider; licensed European fundamentals, exchange quotes, corporate actions,
estimates and sourced FX rates still require selection of authoritative
providers, their usage licences, and credentials. Do not mark those parts
of #19/#21/#22 as fully verified before integration tests against the chosen
real sources. The old `/financials` view remains fail-closed until complete,
reconciled statements can be built from the underlying source facts.
