"""SEC parsing tests use offline response fixtures, never live network."""
import json
from datetime import date, datetime, timezone
from urllib.error import HTTPError

import pytest

from app.modules.ingestion import providers


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, count):
        return json.dumps(self.payload).encode()


def test_sec_companyfacts_preserves_source_and_excludes_ytd(monkeypatch):
    data = {
        "cik": 1234, "entityName": "Example issuer",
        "facts": {"us-gaap": {"Revenues": {"units": {"USD": [
            {"form": "10-K", "accn": "2025-annual", "start": "2025-01-01",
             "end": "2025-12-31", "filed": "2026-02-01", "fy": 2025,
             "fp": "FY", "val": 1000},
            {"form": "10-Q", "accn": "2025-Q2", "start": "2025-01-01",
             "end": "2025-06-30", "filed": "2025-08-01", "fy": 2025,
             "fp": "Q2", "val": 500},
            {"form": "10-Q", "accn": "2025-Q2", "start": "2025-04-01",
             "end": "2025-06-30", "filed": "2025-08-01", "fy": 2025,
             "fp": "Q2", "val": 260},
        ]}}}},
    }
    monkeypatch.setattr(providers, "urlopen", lambda request, timeout: FakeResponse(data))
    rows = providers.SecCompanyFactsProvider("researcher contact@example.com").collect("1234")
    assert rows.evidence.source_url.endswith("CIK0000001234.json")
    assert rows.evidence.provider == "sec_edgar"
    assert {x.raw_value for x in rows.facts} == {1000, 260}
    assert {x.period_type for x in rows.facts} == {"annual", "quarterly"}
    assert all(x.fiscal_quarter is None for x in rows.facts if x.period_type == "annual")


def test_sec_requires_explicit_cik_and_operator_contact():
    with pytest.raises(providers.ProviderUnavailable):
        providers.SecCompanyFactsProvider("")
    client = providers.SecCompanyFactsProvider("researcher contact@example.com")
    with pytest.raises(ValueError):
        client.collect("NVDA")


def test_provider_rate_limit_is_a_bounded_retry(monkeypatch):
    def rate_limited(request, timeout):
        raise HTTPError(request.full_url, 429, "rate limit", {"Retry-After": "120"}, None)

    monkeypatch.setattr(providers, "urlopen", rate_limited)
    client = providers.SecCompanyFactsProvider("researcher contact@example.com")
    with pytest.raises(providers.ProviderRateLimited) as exc:
        client.collect("1234")
    assert exc.value.retry_after == 120
