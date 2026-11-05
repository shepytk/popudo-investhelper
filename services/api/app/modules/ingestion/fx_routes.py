"""Dated ECB EUR reference rates exposed with immutable source evidence."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FxObservation, SourceSnapshot
from app.modules.companies.errors import domain_error
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/fx", tags=["sourced-fx"])


class EurReferenceOut(BaseModel):
    base_currency: str
    quote_currency: str
    eur_to_quote: Decimal
    observed_date: date
    source_url: str
    source_sha256: str
    provider: str
    as_of: date


@router.get("/eur-reference", response_model=EurReferenceOut)
def eur_reference(
    currency: str = Query(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"),
    as_of: date = Query(),
    db: Session = Depends(get_db),
):
    """One EUR in the requested quote currency; caller performs explicit division."""
    if as_of > date.today():
        raise domain_error(422, "invalid_as_of", "Future FX fixing is not permitted")
    if currency == "EUR":
        raise domain_error(422, "invalid_currency", "EUR-to-EUR has no sourced fixing")
    latest = db.execute(
        select(FxObservation, SourceSnapshot)
        .join(SourceSnapshot, FxObservation.source_snapshot_id == SourceSnapshot.id)
        .where(FxObservation.provider == "ecb_fx")
        .where(FxObservation.base_currency == "EUR")
        .where(FxObservation.quote_currency == currency)
        .where(FxObservation.observed_date <= as_of)
        .where(FxObservation.observed_date >= as_of - timedelta(days=5))
        .order_by(FxObservation.observed_date.desc(), FxObservation.revision.desc(), FxObservation.id.desc())
        .limit(1)
    ).first()
    if latest is None:
        raise domain_error(404, "missing_data", "No recent sourced ECB fixing for this currency and date")
    rate, evidence = latest
    if not evidence.source_url.startswith("https://") or not evidence.content_hash or rate.rate <= 0:
        raise domain_error(422, "invalid_provenance", "ECB fixing lacks valid sourcing")
    return EurReferenceOut(
        base_currency="EUR", quote_currency=currency,
        eur_to_quote=rate.rate, observed_date=rate.observed_date,
        provider="ecb_fx", source_url=evidence.source_url,
        source_sha256=evidence.content_hash, as_of=as_of,
    )
