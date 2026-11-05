"""Cheap deterministic contract checks for P3 UX and source safety."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "apps/web/src/app/companies/[id]/page.tsx"
STATUS = ROOT / "apps/web/src/components/research-data-status.tsx"
CHART = ROOT / "apps/web/src/components/financial-trend.tsx"
SCREENER = ROOT / "apps/web/src/app/screener/page.tsx"
TRACE = ROOT / "apps/web/src/components/calculation-trace.tsx"
EUR = ROOT / "apps/web/src/components/eur-quote.tsx"


def test_p3_markup_contract() -> None:
    page = PAGE.read_text()
    status = STATUS.read_text()
    chart = CHART.read_text()
    screener = SCREENER.read_text()
    trace = TRACE.read_text()
    eur = EUR.read_text()
    for topic in ("Issuer", "Listings", "Market quotations", "Financial statements"):
        assert f'subject="{topic}"' in page, topic
    assert 'role={code === "empty" || code === "missing_data" ? "status" : "alert"}' in status
    for code in ("stale_data", "provider_unavailable", "invalid_provenance", "not_computable"):
        assert f"{code}:" in status
    assert 'role="region"' in page and 'overflow-x-auto' in page
    assert 'aria-labelledby="financial-chart-title financial-chart-desc"' in chart
    assert 'if (annual.length < 2 || currencies.size !== 1' in chart
    assert "if (numbers.length !== annual.length * METRICS.length)" in chart
    assert 'role="search"' in screener and 'aria-label="Screening pagination"' in screener
    assert 'role="region"' in screener and 'min-h-11' in screener
    assert "Math.abs(cash - capex - fcf) <= 0.01" in trace
    for concept in ("Free cash flow", "Net debt", "Price / earnings", "Enterprise value", "DCF"):
        assert concept in trace
    assert "Indicative EUR conversion unavailable" in eur
    assert "fx.observed_date" in eur and "fx.source_sha256" in eur
    assert "ECB reference rate" in eur


if __name__ == "__main__":
    test_p3_markup_contract()
    print("P3 research UI structural contract passed")
