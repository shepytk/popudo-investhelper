from datetime import date
from decimal import Decimal

import pytest

from app.modules.companies.normalization import (
    normalize_amount, normalize_capex, normalize_currency, validate_period,
)


def test_normalize_units_exactly():
    assert normalize_amount("1.234", "millions") == Decimal("1234000.000")
    assert normalize_amount("2500.5", "thousands") == Decimal("2500500.0")
    assert normalize_currency("eur") == "EUR"
    assert normalize_capex("-1.2", "millions") == Decimal("1200000.0")


def test_cannot_silently_guess_units_currency_or_nonfinite_money():
    for value, unit in [("1", "unknown"), ("NaN", "ones"), ("Infinity", "thousands")]:
        with pytest.raises(ValueError):
            normalize_amount(value, unit)
    with pytest.raises(ValueError):
        normalize_currency("EURO")


def test_reject_inconsistent_fiscal_period():
    validate_period("annual", 2025, None, date(2025, 12, 31))
    validate_period("quarterly", 2025, 4, date(2025, 12, 31))
    with pytest.raises(ValueError):
        validate_period("annual", 2025, 4, date(2025, 12, 31))
    with pytest.raises(ValueError):
        validate_period("quarterly", 2025, None, date(2025, 12, 31))
