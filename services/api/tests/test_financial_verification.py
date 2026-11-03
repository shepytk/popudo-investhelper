from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.modules.companies.verification import validate_statement


def statement(**overrides):
    data = dict(
        source="annual_report",
        source_url="https://company.example.com/2025/annual.pdf",
        reporting_currency="EUR",
        amount_unit="ones",
        published_date=date(2026, 2, 1),
        retrieved_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        period_end_date=date(2025, 12, 31),
        period_type="annual",
        revenue=1000,
        gross_profit=600,
        operating_income=300,
        net_income=210,
        total_assets=3000,
        total_liabilities=1500,
        total_equity=1500,
        cash_and_equivalents=100,
        total_debt=500,
        operating_cash_flow=280,
        capital_expenditure=80,
        free_cash_flow=200,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def test_valid_normalized_statement():
    assert validate_statement(statement(), today=date(2026, 11, 3)) == []


def test_seed_and_missing_metadata_rejected():
    errors = validate_statement(
        statement(source="seed", source_url=None, reporting_currency=None,
                  retrieved_at=None, amount_unit="millions"),
        today=date(2026, 11, 3),
    )
    assert {"unverified_source", "missing_source_url",
            "missing_reporting_currency", "missing_retrieval_timestamp",
            "non_normalized_amount_unit"}.issubset(set(errors))


def test_unreconciled_cash_flow_rejected():
    errors = validate_statement(statement(free_cash_flow=220), today=date(2026, 11, 3))
    assert "free_cash_flow_reconciliation_failed" in errors


def test_future_publication_and_stale_statement_rejected():
    errors = validate_statement(
        statement(period_end_date=date(2023, 12, 31), published_date=date(2027, 2, 1)),
        today=date(2026, 11, 3),
    )
    assert "missing_or_future_publication_date" in errors
    assert "stale_financial_statement" in errors


def test_quarterly_facts_have_shorter_freshness_window():
    errors = validate_statement(
        statement(period_type="quarterly", period_end_date=date(2025, 12, 31)),
        today=date(2026, 11, 3),
    )
    assert "stale_financial_statement" in errors
