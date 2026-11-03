"""Offline tests for source snapshots, identifiers, precision and idempotency."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base, Company, Country, ExternalIdentifier, FinancialFact, Industry,
    IngestionJob, Sector, SourceSnapshot,
)
from app.modules.companies.facts import facts_as_of
from app.modules.ingestion.calculations import convert_fx, trailing_twelve_months
from app.modules.ingestion.contracts import Evidence, ProviderBatch, ProviderFact, ProviderListing
from app.modules.ingestion.identity import register_listing, valid_isin
from app.modules.ingestion.jobs import claim, enqueue
from app.modules.ingestion.pipeline import import_batch
from app.modules.ingestion.storage import FileSnapshotStore


@pytest.fixture
def context(tmp_path):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    with factory.begin() as db:
        country = Country(name="United States", iso_code="USA", currency_code="USD", region="North America")
        sector = Sector(name="Technology", description="")
        db.add_all([country, sector])
        db.flush()
        industry = Industry(sector_id=sector.id, name="Software", description="")
        db.add(industry)
        db.flush()
        company = Company(
            name="Example", ticker="EXM", isin="", exchange="NYSE",
            country_id=country.id, sector_id=sector.id, industry_id=industry.id,
            currency_code="USD", website_url="", investor_relations_url="",
            description="Test issuer",
        )
        db.add(company)
        db.flush()
        company_id = company.id
    yield factory, company_id, FileSnapshotStore(tmp_path)
    engine.dispose()


def batch(*, raw=b"official report v1", amount="1.234", filing="a1"):
    retrieved_at = datetime.now(timezone.utc) - timedelta(hours=1)
    evidence = Evidence(
        provider="sec_edgar", document_id="CIK0000001234-companyfacts",
        source_url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000001234.json",
        published_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        retrieved_at=retrieved_at, content_type="application/json", raw=raw,
    )
    fact = ProviderFact(
        fact_id="a1:Revenue:2025", filing_version=filing, concept="revenue",
        raw_value=Decimal(amount), raw_unit="millions", currency="USD",
        fiscal_year=2025, fiscal_quarter=None, period_type="annual",
        period_start=date(2025, 1, 1), period_end=date(2025, 12, 31),
        reported_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    return ProviderBatch(evidence=evidence, facts=(fact,))


def test_import_is_idempotent_and_preserves_exact_source(context):
    factory, company_id, store = context
    with factory.begin() as db:
        assert import_batch(db, company_id, batch(), store)["facts"] == 1
    with factory.begin() as db:
        assert import_batch(db, company_id, batch(), store)["facts"] == 0
        row = db.scalar(select(FinancialFact))
        snapshot = db.scalar(select(SourceSnapshot))
        assert row.normalized_value == Decimal("1234000")
        assert row.currency_code == "USD"
        assert snapshot.content_hash in snapshot.object_key
        assert store.get(snapshot.object_key) == b"official report v1"
        assert len(list(db.scalars(select(FinancialFact)))) == 1


def test_reject_conflicting_filing_version(context):
    factory, company_id, store = context
    with factory.begin() as db:
        import_batch(db, company_id, batch(), store)
    with pytest.raises(ValueError, match="Conflicting filing"):
        with factory.begin() as db:
            import_batch(db, company_id, batch(raw=b"amended data", amount="2"), store)


def test_point_in_time_never_peeks_forward(context):
    factory, company_id, store = context
    with factory.begin() as db:
        import_batch(db, company_id, batch(), store)
        before_filing = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert facts_as_of(db, company_id, before_filing) == []
        now = datetime.now(timezone.utc)
        rows = facts_as_of(db, company_id, now)
        assert len(rows) == 1
        assert rows[0][0].concept == "revenue"


def test_identity_checks_valid_isin_and_exchange_scope(context):
    factory, company_id, store = context
    assert valid_isin("US0378331005")
    assert not valid_isin("US0378331004")
    with factory.begin() as db:
        import_batch(db, company_id, batch(), store)
        snapshot = db.scalar(select(SourceSnapshot))
        first = register_listing(db, company_id, ProviderListing(
            security_type="equity", share_class="ordinary",
            isin="US0378331005", mic="XNAS", symbol="EXM",
            currency="USD", is_adr=False, valid_from=date(2020, 1, 1),
        ), snapshot)
        second = register_listing(db, company_id, ProviderListing(
            security_type="equity", share_class="ordinary",
            isin="US0378331005", mic="XNYS", symbol="EXM",
            currency="USD", is_adr=False, valid_from=date(2020, 1, 1),
        ), snapshot)
        assert first.id != second.id
        assert first.security_id == second.security_id


def test_ttm_rejects_ytd_and_mixed_currency():
    end_dates = [date(2025, 3, 31), date(2025, 6, 30),
                 date(2025, 9, 30), date(2025, 12, 31)]
    starts = [date(2025, 1, 1), date(2025, 4, 1),
              date(2025, 7, 1), date(2025, 10, 1)]
    data = [SimpleNamespace(
        concept="revenue", fiscal_year=2025, fiscal_quarter=i + 1,
        period_type="quarterly", period_start=starts[i], period_end=end_dates[i],
        currency_code="EUR", normalized_value=Decimal("100.125"),
    ) for i in range(4)]
    assert trailing_twelve_months(data, "revenue", fiscal_year=2025) == Decimal("400.500")
    data[1].currency_code = "USD"
    with pytest.raises(ValueError, match="mixed"):
        trailing_twelve_months(data, "revenue", fiscal_year=2025)
    data[1].currency_code = "EUR"
    data[1].period_start = date(2025, 1, 1)
    with pytest.raises(ValueError, match="discrete"):
        trailing_twelve_months(data, "revenue", fiscal_year=2025)


def test_fx_rejects_lookahead_and_stale_conversion():
    fx = SimpleNamespace(
        base_currency="USD", quote_currency="EUR",
        observed_date=date(2026, 11, 2), rate=Decimal("0.9"),
    )
    assert convert_fx(Decimal("12.34"), "USD", "EUR", fx, as_of=date(2026, 11, 3)) == Decimal("11.106")
    with pytest.raises(ValueError, match="Lookahead"):
        convert_fx(Decimal("12"), "USD", "EUR", fx, as_of=date(2026, 10, 31))
    with pytest.raises(ValueError, match="Stale"):
        convert_fx(Decimal("12"), "USD", "EUR", fx, as_of=date(2026, 11, 10))


def test_queue_requires_attested_company_mapping(context):
    factory, company_id, store = context
    with factory.begin() as db:
        with pytest.raises(ValueError, match="verified"):
            enqueue(db, company_id, "sec_edgar", "0000001234")
        import_batch(db, company_id, batch(), store)
        snapshot = db.scalar(select(SourceSnapshot))
        db.add(ExternalIdentifier(
            company_id=company_id, provider="sec_edgar",
            provider_company_id="0000001234",
            source_snapshot_id=snapshot.id,
            verified_at=datetime.now(timezone.utc),
        ))
    with factory.begin() as db:
        job = enqueue(db, company_id, "sec_edgar", "0000001234")
        assert job.id == enqueue(db, company_id, "sec_edgar", "0000001234").id
        db.flush()
        job_id = job.id
    with factory.begin() as db:
        selected = claim(db)
        assert selected.id == job_id
        assert selected.attempts == 1
