import json
import logging

from app.observability import HttpMetrics, audit_calculation


def test_metrics_aggregate_bounded_route_and_redact_query(caplog):
    recorder = HttpMetrics(emit_every=3)
    with caplog.at_level(logging.INFO, logger="investhelper.audit"):
        recorder.observe("/api/companies/{company_id}", "GET", 200, 10)
        recorder.observe("/api/companies/{company_id}", "GET", 200, 20)
        assert not caplog.records
        recorder.observe("/api/companies/{company_id}?access_token=secret", "GET", 503, 30)
    rows = [json.loads(r.message) for r in caplog.records]
    assert len(rows) == 2
    successful = next(row for row in rows if row["status_class"] == "2xx")
    assert successful["count"] == 2
    assert successful["latency_total_ms"] == 30
    assert successful["latency_max_ms"] == 20
    failed = next(row for row in rows if row["status_class"] == "5xx")
    assert failed["route"] == "<unmatched>"
    assert failed["error_count"] == 1
    assert "secret" not in "\n".join(r.message for r in caplog.records)


def test_calculation_audit_tracks_version_and_source_without_financial_values(caplog):
    with caplog.at_level(logging.INFO, logger="investhelper.audit"):
        audit_calculation(run_id="run-1", version="dcf-v1",
                          source="manual", outcome="ok",
                          snapshot_hash="a" * 64)
    row = json.loads(caplog.records[-1].message)
    assert row["event"] == "valuation.calculation"
    assert row["calculation_run_id"] == "run-1"
    assert row["calculation_version"] == "dcf-v1"
    assert row["snapshot_sha256"] == "a" * 64
    assert "cash_flow" not in row


def test_invalid_metrics_interval():
    import pytest
    with pytest.raises(ValueError):
        HttpMetrics(0)
