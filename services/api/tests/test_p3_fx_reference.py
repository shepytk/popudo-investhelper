"""Offline acceptance tests for dated, source-verified ECB reference conversions."""
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, FxObservation, SourceSnapshot
from app.modules.ingestion.fx_routes import eur_reference


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def save_rate(db, day: date, *, currency="USD", rate="1.10"):
    snapshot = SourceSnapshot(
        provider="ecb_fx", provider_document_id="ecb-90d",
        source_url="https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml",
        content_hash="f" * 64, object_key="ecb/f",
        retrieved_at=datetime.now(), content_type="application/xml",
    )
    db.add(snapshot)
    db.flush()
    db.add(FxObservation(
        provider="ecb_fx", source_snapshot_id=snapshot.id,
        observed_date=day, base_currency="EUR", quote_currency=currency,
        rate=Decimal(rate), revision="original",
    ))
    db.commit()


def test_rate_has_same_date_and_provenance(db):
    today = date.today()
    save_rate(db, today - timedelta(days=1))
    result = eur_reference(currency="USD", as_of=today, db=db)
    assert result.base_currency == "EUR"
    assert result.quote_currency == "USD"
    assert result.eur_to_quote == Decimal("1.1")
    assert result.observed_date == today - timedelta(days=1)
    assert result.source_sha256 == "f" * 64


def test_unavailable_rate_does_not_invent_parity(db):
    with pytest.raises(HTTPException) as exc:
        eur_reference(currency="CHF", as_of=date.today(), db=db)
    assert exc.value.status_code == 404


def test_stale_rate_is_rejected(db):
    today = date.today()
    save_rate(db, today - timedelta(days=8))
    with pytest.raises(HTTPException) as exc:
        eur_reference(currency="USD", as_of=today, db=db)
    assert exc.value.status_code == 404


def test_future_as_of_rejected(db):
    with pytest.raises(HTTPException) as exc:
        eur_reference(currency="USD", as_of=date.today() + timedelta(days=1), db=db)
    assert exc.value.status_code == 422
