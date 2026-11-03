"""Read-only, time-aware research endpoints over verified source facts."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Security, SecurityListing
from app.modules.companies.fact_schemas import FactPageOut, SourcedFactOut
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
        raise HTTPException(status_code=404, detail={"code": "company_not_found", "message": "Unknown company"})
    cutoff = as_of or datetime.now(timezone.utc)
    if cutoff.tzinfo is None:
        raise HTTPException(status_code=422, detail={"code": "invalid_as_of", "message": "as_of must specify a timezone"})
    if cutoff > datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail={"code": "invalid_as_of", "message": "Future as_of is not supported"})
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
    return FactPageOut(items=items, as_of=cutoff, limit=limit, offset=offset)


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
