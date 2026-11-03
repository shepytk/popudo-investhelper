"""Deterministic, source-backed financial summary. No LLM or fabricated scores."""
from datetime import timezone
from decimal import Decimal
from hashlib import sha256

from app.models import Company, FinancialStatement

DISCLAIMER = "This is investment research support, not financial advice."


def generate_verified_insight(company: Company, annual: FinancialStatement) -> tuple[dict, str]:
    """Report verified facts only. Valuation and recommendations remain unavailable."""
    revenue = Decimal(str(annual.revenue))
    net_income = Decimal(str(annual.net_income))
    free_cash_flow = Decimal(str(annual.free_cash_flow))
    cash = Decimal(str(annual.cash_and_equivalents))
    debt = Decimal(str(annual.total_debt))
    currency = annual.reporting_currency
    year = annual.fiscal_year
    margin = (free_cash_flow / revenue * 100) if revenue > 0 else None
    def amount(number: Decimal) -> str:
        return f"{number:,.2f} {currency}"
    profitability = f"Net income: {amount(net_income)}; free cash flow: {amount(free_cash_flow)}."
    if margin is not None:
        profitability += f" FCF/revenue: {margin:.2f}%."
    balance = f"Cash and equivalents: {amount(cash)}; reported total debt: {amount(debt)}; net debt: {amount(debt - cash)}."
    observed = annual.retrieved_at
    observed_utc = observed.replace(tzinfo=timezone.utc) if observed.tzinfo is None else observed.astimezone(timezone.utc)
    evidence = [{
        "metric_period": annual.period_end_date.isoformat(),
        "published_date": annual.published_date.isoformat(),
        "retrieved_at": observed_utc.isoformat(),
        "source": annual.source,
        "source_url": annual.source_url,
        "reporting_currency": currency,
        "amount_unit": annual.amount_unit,
    }]
    provenance = "|".join((str(company.id), str(annual.id), annual.source_url, observed_utc.isoformat()))
    snapshot = sha256(provenance.encode("utf-8")).hexdigest()
    payload = {
        "status": "partial_verified",
        "as_of": annual.period_end_date.isoformat(),
        "evidence": evidence,
        "summary": f"{company.name}: fiscal {year} annual facts from {annual.source}. Valuation and investment ranking are not available.",
        "business_model": company.description or "Business-model analysis is not available from verified filings.",
        "quality_view": profitability,
        "growth_view": "Not computable: a verified multi-period growth model is not implemented.",
        "valuation_view": "Not computable: verified market price, shares outstanding and valuation assumptions are required.",
        "balance_sheet_view": balance,
        "risk_view": "No risk score or investment recommendation is available. Review the source filing independently.",
        "opportunities": [],
        "risks": [],
        "questions_for_further_research": [
            "What are the changes in revenue and margins across several audited periods?",
            "How do capex, debt maturity and share count affect intrinsic value?",
        ],
        "disclaimer": DISCLAIMER,
    }
    return payload, snapshot
