# Feature Spec: Country → Sector → Company Research Flow

## Feature type

Customer-facing capability

## Requirements

1. User can choose a country and view related sectors.
2. User can open a sector and view companies in that sector.
3. User can open a company profile and view fundamentals.
4. User can request AI insight from company fundamentals.

## User scenarios

- As an investor, I select a country and quickly see investable sectors.
- As an investor, I open a sector and see companies without fragmented loading.
- As an investor, I open one company page and review key financial data.
- As an investor, I generate an AI summary with a disclaimer for research use.

## Architecture

- Layers impacted: Presentation, Application/API, Domain, Data Access.
- Primary API contracts:
  - `GET /api/countries`
  - `GET /api/countries/{countryId}/sectors`
  - `GET /api/sectors/with-companies`
  - `GET /api/companies/{companyId}`
  - `GET /api/companies/{companyId}/financials`
  - `POST /api/ai/companies/{companyId}/generate-insight`

## Backend spec

- Keep query behavior deterministic and safe (escaped search wildcards).
- Return normalized read models for sector/company/fundamentals views.
- Persist generated insight payloads with research question context.

## UI spec

- Provide country/sector/company traversal with clear navigation.
- Render fundamentals in structured tabular format.
- Allow insight generation action and render structured output.
- Always show guardrail/disclaimer context near generated insight.

## Acceptance criteria

- User can complete full Country → Sector → Company → Fundamentals → AI flow.
- API responses are stable and mapped directly to UI data needs.
- No UI step requires direct DB access or backend internals.
