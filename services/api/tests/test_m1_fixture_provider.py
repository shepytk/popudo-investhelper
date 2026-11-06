"""Fixture adapter contract and isolation tests; no DB or network required."""
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.ingestion.contracts import FinancialDataProvider
from app.modules.ingestion.fixture_provider import FixtureFinancialDataProvider
from app.modules.ingestion.providers import ProviderUnavailable, provider_from_environment


FIXTURE = Path(__file__).parent / "fixtures" / "m1_sample_issuer.json"


def test_provider_obeys_contract_and_is_deterministic():
    provider = FixtureFinancialDataProvider(FIXTURE, environment="test")
    assert isinstance(provider, FinancialDataProvider)
    first = provider.collect("OFFLINE-ISSUER-1")
    second = provider.collect("OFFLINE-ISSUER-1")
    assert first == second
    assert first.evidence.provider == "fixture"
    assert first.evidence.raw == FIXTURE.read_bytes()
    assert len(first.facts) == 3
    assert first.facts[0].raw_value == Decimal("1250000000.00")
    assert first.listings[0].isin is None


def test_fixture_never_registers_as_production_provider():
    with pytest.raises(ProviderUnavailable):
        provider_from_environment("fixture")
    with pytest.raises(RuntimeError, match="disabled"):
        FixtureFinancialDataProvider(FIXTURE, environment="production")


def test_subject_mismatch_is_rejected():
    provider = FixtureFinancialDataProvider(FIXTURE, environment="test")
    with pytest.raises(ValueError, match="does not match"):
        provider.collect("WRONG")
    with pytest.raises(ValueError, match="Invalid"):
        provider.collect("../m1_sample_issuer")


def test_non_finite_values_are_rejected(tmp_path):
    payload = json.loads(FIXTURE.read_text())
    payload["facts"][0]["raw_value"] = "NaN"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="finite"):
        FixtureFinancialDataProvider(path, environment="test").collect("OFFLINE-ISSUER-1")


def test_fixture_is_untrusted_evidence():
    batch = FixtureFinancialDataProvider(FIXTURE, environment="test").collect("OFFLINE-ISSUER-1")
    assert batch.evidence.provider == "fixture"
    assert batch.evidence.source_url.startswith("https://fixtures.invalid/")
