"""Fail-closed checks for financial facts used by investment research.

Only normalized values in individual currency units ("ones") and carrying
inspectable, dated provenance can enter screens or insight generation.
A nonempty source label by itself does not constitute verification.
"""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from app.models import FinancialStatement

BLOCKED_SOURCES = frozenset({"seed", "mock", "test", "fixture", "demo", "synthetic", "unknown"})
MAX_ANNUAL_AGE_DAYS = 550
MAX_QUARTERLY_AGE_DAYS = 210


def validate_statement(item: FinancialStatement, *, today: date | None = None) -> list[str]:
    today = today or datetime.now(timezone.utc).date()
    errors: list[str] = []
    if not item.source or item.source.strip().lower() in BLOCKED_SOURCES:
        errors.append("unverified_source")
    url = urlsplit(item.source_url or "")
    if url.scheme != "https" or not url.hostname:
        errors.append("missing_source_url")
    if not item.reporting_currency or len(item.reporting_currency) != 3 or not item.reporting_currency.isalpha() or item.reporting_currency != item.reporting_currency.upper():
        errors.append("missing_reporting_currency")
    if item.amount_unit != "ones":
        errors.append("non_normalized_amount_unit")
    if not item.published_date or item.published_date > today:
        errors.append("missing_or_future_publication_date")
    timestamp = item.retrieved_at
    if not timestamp:
        errors.append("missing_retrieval_timestamp")
    else:
        observed = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc)
        if observed.date() > today:
            errors.append("future_retrieval_timestamp")
    if item.period_end_date > today:
        errors.append("future_reporting_period")
    if item.published_date and item.published_date < item.period_end_date:
        errors.append("publication_before_period_end")
    if item.period_type not in {"annual", "quarterly"}:
        errors.append("unsupported_period_type")
    else:
        maximum = MAX_ANNUAL_AGE_DAYS if item.period_type == "annual" else MAX_QUARTERLY_AGE_DAYS
        if (today - item.period_end_date).days > maximum:
            errors.append("stale_financial_statement")
    numeric_fields = (
        "revenue", "gross_profit", "operating_income", "net_income",
        "total_assets", "total_liabilities", "total_equity", "cash_and_equivalents",
        "total_debt", "operating_cash_flow", "capital_expenditure", "free_cash_flow",
    )
    for field in numeric_fields:
        try:
            val = Decimal(str(getattr(item, field)))
            if not val.is_finite():
                errors.append(f"invalid_{field}")
        except (InvalidOperation, TypeError, ValueError):
            errors.append(f"invalid_{field}")
    if not errors:
        operating = Decimal(str(item.operating_cash_flow))
        capex = Decimal(str(item.capital_expenditure))
        free = Decimal(str(item.free_cash_flow))
        # Normalized capex must be positive cash outflow.
        if capex < 0 or abs((operating - capex) - free) > Decimal("0.02"):
            errors.append("free_cash_flow_reconciliation_failed")
    return errors


def verified_statements(items: list[FinancialStatement], *, today: date | None = None) -> list[FinancialStatement]:
    return [s for s in items if not validate_statement(s, today=today)]
