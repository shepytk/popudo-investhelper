# Speckit Specs

This directory is the source of truth for planning and delivery.

## Working model

- Organize work by **feature**.
- A feature is one of:
  - a customer-facing capability,
  - a backend capability that enables customer value,
  - or an infrastructure support module.
- Every feature spec must include:
  - requirements,
  - user scenarios,
  - architecture notes,
  - backend scope,
  - UI scope.

## Structure

- `layered-architecture.md`: repository-wide architecture contract.
- `features/`: one spec per feature.

## Feature checklist (solid workflow)

1. Define business outcome and scope boundaries.
2. Write user scenarios with acceptance criteria.
3. Define layered architecture impacts.
4. Split implementation tasks into backend and UI work.
5. Implement and validate against acceptance criteria.
