"""Offline ECB XML and sourced cross-currency reference conversion tests."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base, FxObservation, SourceSnapshot
from app.modules.ingestion.ecb_fx import convert_via_eur, import_ecb_fx, parse_ecb_xml
from app.modules.ingestion.storage import FileSnapshotStore

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
 xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
<Cube><Cube time="2026-11-02">
<Cube currency="USD" rate="1.2000"/>
<Cube currency="GBP" rate="0.8000"/>
</Cube></Cube></gesmes:Envelope>"""


def test_parse_and_convert_ecb_reference_rates():
    batch = parse_ecb_xml(XML, datetime(2026, 11, 3, tzinfo=timezone.utc))
    assert batch.evidence.provider == "ecb_fx"
    assert len(batch.fx_rates) == 2
    rates = {x.quote_currency: x.rate for x in batch.fx_rates}
    assert convert_via_eur(Decimal("120"), "USD", "EUR", rates) == Decimal("1.0E+2")
    assert convert_via_eur(Decimal("120"), "USD", "GBP", rates) == Decimal("80")
    with pytest.raises(ValueError, match="missing"):
        convert_via_eur(Decimal("5"), "CHF", "EUR", rates)


def test_import_is_immutable_and_idempotent(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    store = FileSnapshotStore(tmp_path)
    batch = parse_ecb_xml(XML, datetime(2026, 11, 3, tzinfo=timezone.utc))
    with factory.begin() as db:
        assert import_ecb_fx(db, batch, store) == 2
    with factory.begin() as db:
        assert import_ecb_fx(db, batch, store) == 0
        assert len(db.scalars(select(FxObservation)).all()) == 2
        snapshot = db.scalar(select(SourceSnapshot))
        assert store.get(snapshot.object_key) == XML
    engine.dispose()


def test_bad_xml_is_rejected():
    with pytest.raises(ValueError, match="Invalid ECB XML"):
        parse_ecb_xml(b"<!DOCTYPE foo>\n<foo/>", datetime.now(timezone.utc))
    with pytest.raises(ValueError, match="nonfinite ECB rate"):
        parse_ecb_xml(XML.replace(b"1.2000", b"NaN"), datetime.now(timezone.utc))
