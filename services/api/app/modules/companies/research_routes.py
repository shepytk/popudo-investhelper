"""Read-only, time-aware research endpoints over verified source facts."""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, QuoteObservation, Security, SecurityListing, SourceSnapshot
from app.modules.companies.fact_schemas import FactPageOut, SourcedFactOut, SourcedQuoteOut
from app.modules.companies.errors import domain_error
from app.modules.companies.facts import facts_as_of
from app.modules.ingestion.identity_schemas import ListingOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/companies", tags=["sourced-research"])


@router.get("/{company_id}/facts", response_model=FactPageOut)
def get_sourced_facts(
    company_id: int,
    as_of: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if not db.get(Company, company_id):
        raise domain_error(404, "company_not_found", "Unknown company")
    cutoff = as_of or datetime.now(timezone.utc)
    if cutoff.tzinfo is None:
        raise domain_error(422, "invalid_as_of", "as_of must specify a timezone")
    if cutoff > datetime.now(timezone.utc):
        raise domain_error(422, "invalid_as_of", "Future as_of is not supported")
    rows = facts_as_of(db, company_id, cutoff, limit=limit, offset=offset)
    items = [
        SourcedFactOut(
            id=fact.id, concept=fact.concept, period_type=fact.period_type,
            period_start=fact.period_start, period_end=fact.period_end,
            fiscal_year=fact.fiscal_year, fiscal_quarter=fact.fiscal_quarter,
            value=fact.normalized_value, currency_code=fact.currency_code,
            provider=fact.provider, filing_version=fact.filing_version,
            source_url=snapshot.source_url,
            published_at=fact.reported_at, retrieved_at=snapshot.retrieved_at,
            source_sha256=snapshot.content_hash,
        )
        for fact, snapshot in rows
    ]
    return FactPageOut(status="ok" if items else "missing_data", items=items, as_of=cutoff, limit=limit, offset=offset)


@router.get("/{company_id}/listings", response_model=list[ListingOut])
def get_company_listings(
    company_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail={"code": "company_not_found", "message": "Unknown company"})
    stmt = (
        select(SecurityListing)
        .join(Security, SecurityListing.security_id == Security.id)
        .where(Security.company_id == company_id)
        .where(SecurityListing.verified.is_(True))
        .order_by(SecurityListing.mic, SecurityListing.symbol, SecurityListing.id)
        .limit(limit).offset(offset)
    )
    return list(db.scalars(stmt))


@router.get("/{company_id}/quotes", response_model=list[SourcedQuoteOut])
def get_company_quotes(
    company_id: int,
    as_of: datetime | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return sourced recent quotes or an explicit missing/stale data error."""
    if not db.get(Company, company_id):
        raise domain_error(404, "company_not_found", "Unknown company")
    cutoff = as_of or datetime.now(timezone.utc)
    if cutoff.tzinfo is None or cutoff > datetime.now(timezone.utc):
        raise domain_error(422, "invalid_as_of", "Specify a non-future timezone-aware as_of")
    utc_cutoff = cutoff.astimezone(timezone.utc)
    instant = utc_cutoff.replace(tzinfo=None)
    rows = list(db.execute(
        select(QuoteObservation, SecurityListing, SourceSnapshot)
        .join(SecurityListing, QuoteObservation.listing_id == SecurityListing.id)
        .join(Security, SecurityListing.security_id == Security.id)
        .join(SourceSnapshot, QuoteObservation.source_snapshot_id == SourceSnapshot.id)
        .where(Security.company_id == company_id)
        .where(SecurityListing.verified.is_(True))
        .where(QuoteObservation.session_date <= utc_cutoff.date())
        .where(SourceSnapshot.retrieved_at <= instant)
        .order_by(QuoteObservation.session_date.desc(), QuoteObservation.id.desc())
        .limit(limit)
    ))
    if not rows:
        raise domain_error(404, "missing_data", "No source-verified market quotations available", retryable=True)
    latest_date = rows[0][0].session_date
    if (utc_cutoff.date() - latest_date).days > 10:
        raise domain_error(422, "stale_data", "Latest quote is older than 10 calendar days", retryable=True)
    return [
        SourcedQuoteOut(
            listing_id=listing.id, mic=listing.mic, symbol=listing.symbol,
            date=quote.session_date, close=quote.close,
            currency_code=quote.currency_code, provider=quote.provider,
            source_url=snapshot.source_url, source_sha256=snapshot.content_hash,
            retrieved_at=snapshot.retrieved_at,
        )
        for quote, listing, snapshot in rows
        if (utc_cutoff.date() - quote.session_date).days <= 10
    ]
