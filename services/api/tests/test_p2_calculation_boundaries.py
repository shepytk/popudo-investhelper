"""Deterministic offline regression tests for financial arithmetic safety."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.ingestion.calculations import convert_fx, trailing_twelve_months


def rate(*, observed=date(2026, 11, 3), value="0.91", base="USD", quote="EUR"):
    return SimpleNamespace(
        base_currency=base, quote_currency=quote,
        observed_date=observed, rate=Decimal(value),
    )


def test_fx_precision_and_fail_closed_reciprocal():
    assert convert_fx(Decimal("123.45"), "USD", "EUR", rate(), as_of=date(2026, 11, 4)) == Decimal("112.3395")
    with pytest.raises(ValueError, match="pair mismatch"):
        convert_fx(Decimal("100"), "EUR", "USD", rate(), as_of=date(2026, 11, 4))


@pytest.mark.parametrize("observed,as_of,amount,reason", [
    (date(2026, 11, 5), date(2026, 11, 4), "0.91", "Lookahead"),
    (date(2026, 10, 20), date(2026, 11, 4), "0.91", "Stale"),
    (date(2026, 11, 3), date(2026, 11, 4), "0", "Nonpositive"),
])
def test_fx_rejects_unsafe_inputs(observed, as_of, amount, reason):
    with pytest.raises(ValueError, match=reason):
        convert_fx(Decimal("10"), "USD", "EUR", rate(observed=observed, value=amount), as_of=as_of)


def quarters():
    starts = [date(2025, 1, 1), date(2025, 4, 1), date(2025, 7, 1), date(2025, 10, 1)]
    ends = [date(2025, 3, 31), date(2025, 6, 30), date(2025, 9, 30), date(2025, 12, 31)]
    return [
        SimpleNamespace(concept="revenue", fiscal_year=2025, fiscal_quarter=i + 1,
                        period_type="quarterly", period_start=starts[i], period_end=ends[i],
                        currency_code="USD", normalized_value=Decimal("0.01") * (i + 1))
        for i in range(4)
    ]


def test_ttm_exact_decimal_sum():
    assert trailing_twelve_months(quarters(), "revenue", fiscal_year=2025) == Decimal("0.10")


def test_ttm_rejects_duplicate_quarters():
    data = quarters()
    data[-1].fiscal_quarter = 3
    with pytest.raises(ValueError, match="exactly one"):
        trailing_twelve_months(data, "revenue", fiscal_year=2025)


def test_ttm_rejects_ytd_quarter():
    data = quarters()
    data[2].period_start = date(2025, 1, 1)
    with pytest.raises(ValueError, match="discrete"):
        trailing_twelve_months(data, "revenue", fiscal_year=2025)


def test_ttm_rejects_mixed_currencies():
    data = quarters()
    data[1].currency_code = "EUR"
    with pytest.raises(ValueError, match="mixed"):
        trailing_twelve_months(data, "revenue", fiscal_year=2025)
