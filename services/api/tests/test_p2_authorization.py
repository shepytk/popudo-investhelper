"""No identity-provider account is needed to test cross-account ownership."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import Principal, current_user
from app.main import app
from app.models import Base, Company, Country, Industry, Sector
from app.shared.database.session import get_db


@pytest.fixture
def auth_client():
    engine = create_engine("sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as db:
        country = Country(name="USA", iso_code="USA", currency_code="USD", region="NA")
        sector = Sector(name="Technology", description="")
        db.add_all([country, sector])
        db.flush()
        industry = Industry(name="Software", description="", sector_id=sector.id)
        db.add(industry)
        db.flush()
        db.add(Company(
            name="Example", ticker="EXM", isin="", exchange="XNAS",
            country_id=country.id, sector_id=sector.id, industry_id=industry.id,
            currency_code="USD", description="", website_url="", investor_relations_url="",
        ))
    principal = {"id": "alice"}

    def database():
        with factory() as db:
            yield db

    def whoami():
        return Principal(user_id=principal["id"])

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[current_user] = whoami
    try:
        with TestClient(app) as client:
            yield client, principal
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(current_user, None)
        engine.dispose()


def test_cross_account_read_write_and_delete_are_denied(auth_client):
    client, principal = auth_client
    created = client.post("/api/me/watchlists", json={"name": "My stocks"})
    assert created.status_code == 201, created.text
    wid = created.json()["id"]
    assert client.post(f"/api/me/watchlists/{wid}/items", json={"company_id": 1}).status_code == 201
    principal["id"] = "bob"
    assert client.get("/api/me/watchlists").json() == []
    for method, path, payload in [
        ("get", f"/api/me/watchlists/{wid}", None),
        ("get", f"/api/me/watchlists/{wid}/items", None),
        ("post", f"/api/me/watchlists/{wid}/items", {"company_id": 1}),
        ("delete", f"/api/me/watchlists/{wid}/items/1", None),
        ("delete", f"/api/me/watchlists/{wid}", None),
    ]:
        result = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
        assert result.status_code == 404, result.text
    principal["id"] = "alice"
    assert len(client.get(f"/api/me/watchlists/{wid}/items").json()) == 1
    assert client.delete(f"/api/me/watchlists/{wid}").status_code == 204


def test_user_ids_are_not_accepted_from_client(auth_client):
    client, principal = auth_client
    created = client.post("/api/me/watchlists", json={"name": "Mine", "user_id": "victim"})
    assert created.status_code == 201
    principal["id"] = "victim"
    assert client.get("/api/me/watchlists").json() == []


def test_routes_fail_closed_when_oidc_is_unconfigured(monkeypatch):
    monkeypatch.delenv("INVESTHELPER_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("INVESTHELPER_OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("INVESTHELPER_OIDC_JWKS_URL", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/me/watchlists")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "auth_not_configured"
