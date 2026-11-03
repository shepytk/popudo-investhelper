"""Official ECB EUR reference rates, with immutable provenance and no FX guesses.

Reference rates are informational, not executable market quotes. All rates
are stored in ECB's direction (one EUR equals N units of quote currency).
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FxObservation, SourceSnapshot
from app.modules.ingestion.contracts import Evidence, ProviderBatch, ProviderFX, SnapshotStore
from app.modules.ingestion.storage import object_key

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"


def parse_ecb_xml(raw: bytes, retrieved_at: datetime) -> ProviderBatch:
    if not raw or len(raw) > 5_000_000 or b"<!DOCTYPE" in raw.upper():
        raise ValueError("Invalid ECB XML payload")
    root = ElementTree.fromstring(raw)
    if root.tag.split("}")[-1] != "Envelope":
        raise ValueError("Unexpected ECB XML root")
    rows = []
    for element in root.iter():
        if element.tag.split("}")[-1] != "Cube":
            continue
        trading_date = element.attrib.get("time")
        if not trading_date:
            continue
        session = date.fromisoformat(trading_date)
        if session > retrieved_at.date():
            raise ValueError("ECB reported a future exchange-rate date")
        for leaf in element:
            currency, rate_text = leaf.attrib.get("currency"), leaf.attrib.get("rate")
            if not currency or not rate_text or len(currency) != 3 or not currency.isalpha():
                raise ValueError("Malformed ECB rate")
            try:
                rate = Decimal(rate_text)
            except InvalidOperation as exc:
                raise ValueError("Invalid ECB rate") from exc
            if not rate.is_finite() or rate <= 0:
                raise ValueError("Nonpositive or nonfinite ECB rate")
            rows.append(ProviderFX(
                observed_date=session, base_currency="EUR",
                quote_currency=currency, rate=rate,
            ))
    if not rows:
        raise ValueError("ECB XML contains no reference rates")
    evidence = Evidence(
        provider="ecb_fx", document_id="ecb-eurofxref-hist-90d",
        source_url=ECB_URL, published_at=None, retrieved_at=retrieved_at,
        content_type="application/xml", raw=raw,
    )
    return ProviderBatch(evidence=evidence, fx_rates=tuple(rows))


def download_ecb_reference_rates() -> ProviderBatch:
    request = Request(ECB_URL, headers={
        "User-Agent": "PopudoInvestHelper/0.1 (research reference FX)",
        "Accept": "application/xml",
    })
    with urlopen(request, timeout=25) as response:
        raw = response.read(5_000_001)
    return parse_ecb_xml(raw, datetime.now(timezone.utc))


def import_ecb_fx(db: Session, batch: ProviderBatch, store: SnapshotStore) -> int:
    evidence = batch.evidence
    if evidence.provider != "ecb_fx" or evidence.source_url != ECB_URL:
        raise ValueError("Unexpected FX source")
    key, digest = object_key(evidence.provider, evidence.raw)
    store.put_if_absent(key, evidence.raw, evidence.content_type)
    if hashlib.sha256(store.get(key)).hexdigest() != digest:
        raise ValueError("Raw ECB evidence digest mismatch")
    snapshot = db.scalar(select(SourceSnapshot).where(
        SourceSnapshot.provider == evidence.provider,
        SourceSnapshot.provider_document_id == evidence.document_id,
        SourceSnapshot.content_hash == digest,
    ))
    if snapshot is None:
        snapshot = SourceSnapshot(
            provider=evidence.provider, provider_document_id=evidence.document_id,
            source_url=evidence.source_url, content_hash=digest,
            object_key=key, retrieved_at=evidence.retrieved_at,
            published_at=None, content_type=evidence.content_type,
        )
        db.add(snapshot)
        db.flush()
    created = 0
    for item in batch.fx_rates:
        if item.base_currency != "EUR":
            raise ValueError("ECB rates must be quoted against EUR")
        existing = db.scalar(select(FxObservation).where(
            FxObservation.provider == "ecb_fx",
            FxObservation.observed_date == item.observed_date,
            FxObservation.base_currency == item.base_currency,
            FxObservation.quote_currency == item.quote_currency,
            FxObservation.revision == item.revision,
        ))
        if existing is not None:
            if existing.rate != item.rate:
                raise ValueError("ECB correction needs an explicit revision")
            continue
        db.add(FxObservation(
            provider="ecb_fx", source_snapshot_id=snapshot.id,
            observed_date=item.observed_date, base_currency="EUR",
            quote_currency=item.quote_currency, rate=item.rate,
            revision=item.revision,
        ))
        created += 1
    return created


def convert_via_eur(
    amount: Decimal, source_currency: str, target_currency: str,
    rates: dict[str, Decimal],
) -> Decimal:
    """Converts currencies at the same ECB fixing date without a market bid/ask."""
    source_currency = source_currency.upper()
    target_currency = target_currency.upper()
    if source_currency == target_currency:
        return amount
    source = Decimal(1) if source_currency == "EUR" else rates.get(source_currency)
    target = Decimal(1) if target_currency == "EUR" else rates.get(target_currency)
    if source is None or target is None or source <= 0 or target <= 0:
        raise ValueError("Currency missing from sourced ECB fixing")
    return amount / source * target
