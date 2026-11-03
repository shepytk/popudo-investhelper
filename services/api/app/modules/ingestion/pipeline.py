"""Transactional import of complete, hashed source batches."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialFact, SourceSnapshot
from app.modules.companies.normalization import normalize_amount, normalize_currency, validate_period
from app.modules.ingestion.contracts import ProviderBatch, SnapshotStore
from app.modules.ingestion.identity import register_listing
from app.modules.ingestion.storage import object_key


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def import_batch(db: Session, company_id: int, batch: ProviderBatch, store: SnapshotStore) -> dict[str, int]:
    source = batch.evidence
    if not db.get(Company, company_id):
        raise ValueError("Company does not exist")
    if source.provider in {"test", "fixture", "seed", "mock", "demo", "unknown"}:
        raise ValueError("Untrusted demo source")
    url = urlsplit(source.source_url)
    if url.scheme != "https" or not url.hostname or url.username:
        raise ValueError("Source must use HTTPS")
    if not source.raw or not source.document_id:
        raise ValueError("Raw document and provider identifier are required")
    if _utc(source.retrieved_at) > datetime.now(timezone.utc):
        raise ValueError("Future source retrieval time")
    key, digest = object_key(source.provider, source.raw)
    store.put_if_absent(key, source.raw, source.content_type)
    if hashlib.sha256(store.get(key)).hexdigest() != digest:
        raise ValueError("Source object integrity failure")
    snapshot = db.scalar(select(SourceSnapshot).where(
        SourceSnapshot.provider == source.provider,
        SourceSnapshot.provider_document_id == source.document_id,
        SourceSnapshot.content_hash == digest,
    ))
    if snapshot is None:
        snapshot = SourceSnapshot(
            provider=source.provider, source_url=source.source_url,
            provider_document_id=source.document_id, content_hash=digest,
            object_key=key, retrieved_at=_utc(source.retrieved_at),
            published_at=_utc(source.published_at) if source.published_at else None,
            content_type=source.content_type,
        )
        db.add(snapshot)
        db.flush()
    counts = {"facts": 0, "listings": 0}
    for fact in batch.facts:
        validate_period(fact.period_type, fact.fiscal_year, fact.fiscal_quarter, fact.period_end)
        if fact.period_start and fact.period_start > fact.period_end:
            raise ValueError("Fact period is inverted")
        if _utc(fact.reported_at) > _utc(source.retrieved_at):
            raise ValueError("Fact reported after retrieval")
        currency = normalize_currency(fact.currency)
        value = normalize_amount(fact.raw_value, fact.raw_unit)
        existing = db.scalar(select(FinancialFact).where(
            FinancialFact.company_id == company_id,
            FinancialFact.provider == source.provider,
            FinancialFact.provider_fact_id == fact.fact_id,
            FinancialFact.filing_version == fact.filing_version,
        ))
        if existing:
            if existing.normalized_value != value or existing.currency_code != currency:
                raise ValueError("Conflicting filing revision")
            continue
        db.add(FinancialFact(
            company_id=company_id, source_snapshot_id=snapshot.id,
            provider=source.provider, provider_fact_id=fact.fact_id,
            filing_version=fact.filing_version, concept=fact.concept,
            period_type=fact.period_type, period_start=fact.period_start,
            period_end=fact.period_end, fiscal_year=fact.fiscal_year,
            fiscal_quarter=fact.fiscal_quarter, raw_value=fact.raw_value,
            raw_unit=fact.raw_unit, normalized_value=value,
            currency_code=currency, reported_at=_utc(fact.reported_at),
        ))
        counts["facts"] += 1
    db.flush()
    for listing in batch.listings:
        register_listing(db, company_id, listing, snapshot)
        counts["listings"] += 1
    return counts
