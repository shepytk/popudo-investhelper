"""Explicit accounting-unit normalization at the future ingestion boundary.

No FX conversion is performed here: a reporting currency must be preserved,
and mixed-currency financial statements must never be summed without a
dated, sourced FX observation.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

SCALES = {
    "ones": Decimal(1),
    "thousands": Decimal(1000),
    "millions": Decimal(1000000),
    "billions": Decimal(1000000000),
}


def normalize_currency(currency: str) -> str:
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise ValueError("A three-letter reporting currency is required")
    return currency.upper()


def normalize_amount(value: str | int | Decimal, unit: str) -> Decimal:
    if unit not in SCALES:
        raise ValueError(f"Unsupported source amount unit: {unit}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Invalid money amount") from error
    if not number.is_finite():
        raise ValueError("Money amount must be finite")
    return number * SCALES[unit]


def normalize_capex(value: str | int | Decimal, unit: str) -> Decimal:
    """Capital expenditure is normalized to a positive cash outflow."""
    return abs(normalize_amount(value, unit))


def validate_period(period_type: str, fiscal_year: int, quarter: int | None, end: date) -> None:
    if period_type not in {"annual", "quarterly"}:
        raise ValueError("Unsupported financial period")
    if not isinstance(fiscal_year, int) or fiscal_year < 1900 or fiscal_year > end.year + 1:
        raise ValueError("Invalid fiscal year")
    if period_type == "annual" and quarter is not None:
        raise ValueError("Annual reports must not carry a fiscal quarter")
    if period_type == "quarterly" and quarter not in (1, 2, 3, 4):
        raise ValueError("Quarterly reports require Q1–Q4")
