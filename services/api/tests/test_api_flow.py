from fastapi.testclient import TestClient

from app.main import app
from scripts.seed_sample_companies import seed_data
from app.shared.database.session import SessionLocal


client = TestClient(app)


def setup_module() -> None:
    with SessionLocal() as db:
        seed_data(db)


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


def test_company_fundamentals_and_ai_flow() -> None:
    nvidia = client.get("/api/companies/search", params={"q": "NVDA"}).json()[0]

    financials = client.get(f"/api/companies/{nvidia['id']}/financials")
    assert financials.status_code == 200
    assert len(financials.json()) > 0

    insight = client.post(f"/api/ai/companies/{nvidia['id']}/generate-insight")
    assert insight.status_code == 200
    assert insight.json()["disclaimer"] == "This is investment research support, not financial advice."
