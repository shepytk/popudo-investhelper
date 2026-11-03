import os
from datetime import date, datetime, timezone

os.environ["INVESTHELPER_ENV"] = "test"
os.environ["INVESTHELPER_DATABASE_URL"] = "sqlite:///./test-investhelper-p0.db"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import FinancialStatement, Insight
from app.shared.database.session import SessionLocal
from scripts.seed_sample_companies import seed_data

client = TestClient(app)


def setup_module() -> None:
    with SessionLocal() as db:
        seed_data(db, allow_demo=True)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}


def test_sector_to_company_flow() -> None:
    sectors = client.get("/api/sectors").json()
    semis = next((s for s in sectors if s["name"] == "Semiconductors"), None)
    assert semis
    companies = client.get(f"/api/sectors/{semis['id']}/companies").json()
    assert any(c["ticker"] == "NVDA" for c in companies)


def test_unverified_financials_are_not_visible_or_scored() -> None:
    nvidia = client.get("/api/companies/search", params={"q": "NVDA"}).json()[0]
    financials = client.get(f"/api/companies/{nvidia['id']}/financials")
    assert financials.status_code == 200
    assert financials.json() == []
    insight = client.post(f"/api/ai/companies/{nvidia['id']}/generate-insight")
    assert insight.status_code == 422
    assert insight.json()["detail"]["code"] == "not_computable"


def test_verified_financial_statement_produces_factual_insight_without_scores() -> None:
    nvidia = client.get("/api/companies/search", params={"q": "NVDA"}).json()[0]
    company_id = nvidia["id"]
    with SessionLocal() as db:
        # Ensure test is idempotent even when using a local sqlite test file.
        for item in db.scalars(select(FinancialStatement).where(FinancialStatement.company_id == company_id)):
            db.delete(item)
        for item in db.scalars(select(Insight).where(Insight.company_id == company_id)):
            db.delete(item)
        db.commit()
        item = FinancialStatement(
            company_id=company_id, period_type="annual", fiscal_year=2025,
            fiscal_quarter=None, period_end_date=date(2025, 12, 31),
            revenue=1000, gross_profit=500, operating_income=250,
            net_income=200, total_assets=3000, total_liabilities=1500,
            total_equity=1500, cash_and_equivalents=600, total_debt=400,
            operating_cash_flow=230, capital_expenditure=30, free_cash_flow=200,
            source="annual_report", source_url="https://investor.example.com/annual-report",
            reporting_currency="USD", amount_unit="ones",
            published_date=date(2026, 2, 1),
            retrieved_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        )
        db.add(item)
        db.commit()
    try:
        financials = client.get(f"/api/companies/{company_id}/financials")
        assert len(financials.json()) == 1
        assert financials.json()[0]["source_url"] == "https://investor.example.com/annual-report"
        response = client.post(f"/api/ai/companies/{company_id}/generate-insight")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "partial_verified"
        assert "200.00 USD" in body["quality_view"]
        assert "Not computable" in body["valuation_view"]
        assert body["evidence"][0]["reporting_currency"] == "USD"
        with SessionLocal() as db:
            insight = db.scalar(select(Insight).where(Insight.company_id == company_id))
            assert insight is not None
            assert insight.overall_score is None
            assert insight.valuation_score is None
    finally:
        with SessionLocal() as db:
            for item in db.scalars(select(FinancialStatement).where(FinancialStatement.company_id == company_id)):
                db.delete(item)
            for item in db.scalars(select(Insight).where(Insight.company_id == company_id)):
                db.delete(item)
            db.commit()


def test_sectors_with_companies_endpoint() -> None:
    response = client.get("/api/sectors/with-companies")
    assert response.status_code == 200
    assert any(sector["companies"] for sector in response.json())


def test_company_search_escapes_like_wildcards() -> None:
    response = client.get("/api/companies/search", params={"q": "%"})
    assert response.status_code == 200
    assert response.json() == []
