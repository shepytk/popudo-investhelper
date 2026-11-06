# M1: fixture-first, provider-independent ingestion

Tracking: epic #82; stories #87–#91. Initial slice: #87.

## Existing architecture reused
- `FinancialDataProvider.collect(subject) -> ProviderBatch` is the inbound provider port.
- `SnapshotStore` is the immutable evidence storage port.
- `pipeline.import_batch` validates provenance and writes normalized facts transactionally.
- `jobs.work_one` owns retries, leases and orchestration.
- `providers.provider_from_environment` is the **production** adapter registry.

Do not fork these layers or introduce new database schemas before inspecting the existing models and migrations.

## New offline adapter
`FixtureFinancialDataProvider` is explicit-constructor only, reads checked-in JSON, never connects to a provider, never queries a database, and uses fixed evidence timestamps. Its output is an ordinary `ProviderBatch` with evidence provider `fixture`, making it suitable for deterministic provider-contract tests.

Fixture mode is allowed only under `INVESTHELPER_ENV=test` or `development`. **The production registry intentionally does not register it.** `pipeline.import_batch` intentionally rejects `fixture` provenance, so fixture output cannot accidentally become published research data. This first slice is a contract-test harness, *not* a staging seed. An isolated test-data storage path for integration tests can follow without weakening production provenance safeguards.

## Test
```bash
cd services/api
INVESTHELPER_ENV=test PYTHONPATH=. python -m pytest -q tests/test_m1_fixture_provider.py
```

No credentials, network access, database, or MinIO required.

## Planned implementation slices
1. #87 provider contract test harness and selection/license ADR (this PR starts the harness; vendor decision remains pending).
2. #88 verified identity and listing import driven by ports; unit and isolated DB tests.
3. #89 price observation import/reconciliation driven by ports.
4. #90 financial fact normalization/import and evidence snapshots.
5. #91 explicit staging bootstrap and workers using **approved real providers**. Fixtures remain in isolated tests.

## Rules
- Never advertise fixture amounts as real market data.
- Do not add `fixture` to the production registry or public provider redistribution allowlist.
- No inferred ISINs; unknowns remain null.
- Real provider access/approval remains separate from offline tests.
