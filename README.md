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
