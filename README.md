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

**The application is not yet a live stock-data service.** No production financial
provider has been connected. Demo metadata must be imported deliberately,
and no financial-statement fixtures or synthetic ISINs are seeded on API startup.

### Existing database upgrade

For an existing PostgreSQL database, run these scripts in order **before**
deploying this branch:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/migrations/0002_p0_verified_evidence.sql
```

Do not run `0001_initial_schema.sql` again on an existing installation.
New databases created by SQLAlchemy will already have the new fields, but
production-grade versioned migration management is tracked separately (#24).
Before migrating, back up the database. The P0 migration is non-destructive:
it retains historical seed/legacy insights but prevents their reuse in
verified research and clears only exact old fabricated ISIN patterns.

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

The source URL is *metadata*, not cryptographic evidence that the provider
data are accurate. Real vendor import/reconciliation, source authenticity,
multi-period growth, currency conversion, share-class identities and fair-value
models are planned in later work. Never interpret a partial summary as a
completed stock recommendation.

### Regression tests

From the repository root, with Python 3.12 dependencies installed:

```bash
export PYTHONPATH=services/api:.
python -m pytest -q services/api/tests
```

Use a dedicated test database. The suite is designed to reject unverified
and fabricated financial data and avoid persisting hardcoded scoring.
