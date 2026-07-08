# Layered Architecture

## Layers

1. **Presentation Layer**
   - Next.js pages and UI components in `apps/web`.
   - Handles rendering, user input, and UI state.
2. **Application/API Layer**
   - FastAPI routes and request/response orchestration in `services/api`.
   - Exposes use-case oriented endpoints.
3. **Domain Layer**
   - Business entities, validations, and investment logic.
   - Owns rules for Country → Sector → Company → Fundamentals → Insight flow.
4. **Data Access Layer**
   - DB models, queries, migrations, and persistence contracts.
5. **Infrastructure Layer**
   - Postgres, Redis, MinIO, Docker Compose, ingestion runners, and deployment runtime.

## Dependency rule

Dependencies move inward only:

- Presentation → Application/API → Domain → Data Access → Infrastructure adapters.
- Domain logic must not depend on UI framework details.
- UI must consume API contracts, not direct database access.

## Spec policy

Each feature spec under `features/` must explicitly describe:

- impacted layers,
- backend implementation requirements,
- UI implementation requirements,
- test/validation expectations.
