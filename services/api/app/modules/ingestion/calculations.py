"""Pure accounting conversions with explicit sourcing and period alignment."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from collections.abc import Sequence

from app.models import FinancialFact, FxObservation


def convert_fx(
    amount: Decimal, base: str, quote: str, rate: FxObservation,
    *, as_of: date,
) -> Decimal:
    if base == quote:
        return amount
    if (rate.base_currency, rate.quote_currency) != (base, quote):
        raise ValueError("FX pair mismatch; reciprocal rate must be separately sourced")
    if rate.observed_date > as_of:
        raise ValueError("Lookahead FX conversion")
    if (as_of - rate.observed_date).days > 5:
        raise ValueError("Stale FX rate")
    if rate.rate <= 0:
        raise ValueError("Nonpositive FX rate")
    return amount * rate.rate


def trailing_twelve_months(facts: Sequence[FinancialFact], concept: str, *, fiscal_year: int) -> Decimal:
    matching = [f for f in facts if f.concept == concept and f.fiscal_year == fiscal_year
                and f.period_type == "quarterly"]
    if len(matching) != 4 or {x.fiscal_quarter for x in matching} != {1, 2, 3, 4}:
        raise ValueError("TTM needs exactly one fact for each quarter")
    if len({x.currency_code for x in matching}) != 1:
        raise ValueError("Cannot sum mixed reporting currencies")
    if any(x.period_start is None or (x.period_end - x.period_start).days > 105 for x in matching):
        raise ValueError("TTM requires discrete, not year-to-date, quarters")
    ordered = sorted(matching, key=lambda x: x.fiscal_quarter)
    if any(ordered[i].period_end >= ordered[i + 1].period_end for i in range(3)):
        raise ValueError("Fiscal quarters must advance chronologically")
    return sum((x.normalized_value for x in ordered), Decimal(0))
