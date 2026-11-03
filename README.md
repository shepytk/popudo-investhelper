# Fundamental Investment Intelligence Platform (MVP)

This repository now contains a minimal monorepo scaffold for a fundamental investment research platform.

## Implemented MVP baseline

- Monorepo structure for web, API, ingestion, AI engine, packages, infra, docs, and scripts
- Feature-first Speckit specs with layered architecture in `docs/specs`
- Docker Compose with `web`, `api`, `db` (PostgreSQL), `redis`, and `minio`
- FastAPI backend with:
  - `GET /health`
  - `GET /api/countries`
  - `GET /api/countries/{countryId}/sectors`
  - `GET /api/sectors`
  - `GET /api/sectors/{sectorId}/companies`
  - `GET /api/companies/search?q=`
  - `GET /api/companies/{companyId}`
  - `GET /api/companies/{companyId}/financials`
  - `POST /api/ai/companies/{companyId}/generate-insight`
- Initial SQL migration at `infra/migrations/0001_initial_schema.sql`
- Seed scripts for countries, sectors, and sample companies
- Next.js frontend flow for:
  - Sector listing
  - Company profile
  - Fundamentals table
  - AI insight generation

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs

## Local backend test run

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest tests/test_api_flow.py
```

## Seed sample companies

Sample companies seeded by `scripts/seed_sample_companies.py`:

- ASML
- Nvidia
- AMD
- TSMC
- Intel
- Shell
- Adyen
- Prosus
- Vonovia
- SAP

## P0 financial integrity (November 2026)

**The application does not yet provide complete live valuations or exchange quotes.** An opt-in SEC EDGAR adapter now exists for official US XBRL filings, but it requires a verified issuer-to-CIK mapping and operator contact. European coverage needs a provider selection. Demo metadata must be imported deliberately,
and no financial-statement fixtures or synthetic ISINs are seeded on API startup.

### Existing database upgrade and startup (P1)

Versioned migrations now run through `scripts/migrate.py`; the API no
longer creates database tables on import. The Docker Compose API entrypoint
runs migrations before launching FastAPI. Back up any existing PostgreSQL DB.

```bash
export PYTHONPATH=services/api:.
export INVESTHELPER_DATABASE_URL='postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB'
python scripts/migrate.py
python scripts/check_schema.py
```

This applies the initial schema, the P0 safeguards and all P1 changes
transactionally and records checksums. It is safe to re-run with unchanged
migration files. **Never rewrite migration files after deployment.**

For the full architecture, operator workflow, verified SEC CIK linking,
storage configuration and acceptance tests, see
[`docs/specs/features/p1-data-platform.md`](docs/specs/features/p1-data-platform.md).

### Optional demo company metadata

Demo *company names only* can be loaded explicitly in a local development
environment; **no fabricated financial statements** are inserted:

```bash
export INVESTHELPER_ENV=development
export PYTHONPATH=services/api:.
python -m scripts.seed_sample_companies
```

Do not enable this in production. Unknown ISINs are saved as empty strings,
not invented identifiers.

### Verified research requirements

A financial statement must have: a non-demo provider label, HTTPS source URL,
original reporting currency, normalized monetary units (`ones`), dated
publication and retrieval metadata, a recent reporting period, finite
financial values and reconciled free cash flow (OCF minus positive capex).
Unsupported, missing and stale observations are filtered from the public API.

The legacy `POST /api/ai/companies/{id}/generate-insight` now produces
a deterministic **partial verified research summary**, not AI forecasts.
It returns HTTP 422 with `code=not_computable` when no acceptable annual
statement exists. Any summary clearly marks valuation/price targets as
not computable. Generated scores remain NULL and historical mock insights
are excluded from `GET /api/ai/companies/{id}/insights`.

Source URLs alone do not authenticate numbers. The P1 source ingestion flow
hashes raw provider documents, stores a retrieval-time snapshot, and allows
point-in-time reads of imported facts. Complete statement synthesis, European
vendor integration and fair-value models remain separate work. Never interpret a partial summary as a
completed stock recommendation.

### Regression tests

From the repository root, with Python 3.12 dependencies installed:

```bash
export PYTHONPATH=services/api:.
python -m pytest -q services/api/tests
```

Use a dedicated test database. The suite is designed to reject unverified
and fabricated financial data and avoid persisting hardcoded scoring.
