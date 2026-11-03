"""Exchange-scoped securities and verifiable ISINs; never synthesize identifiers."""
from __future__ import annotations

from datetime import date
from urllib.parse import urlsplit

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Security, SecurityListing, SourceSnapshot
from app.modules.ingestion.contracts import ProviderListing


def valid_isin(isin: str) -> bool:
    isin = isin.strip().upper()
    if len(isin) != 12 or not isin[:2].isalpha() or not isin[2:11].isalnum() or not isin[-1].isdigit():
        return False
    expanded = "".join(str(ord(c) - 55) if c.isalpha() else c for c in isin)
    digits = list(map(int, expanded))
    return sum((n * (2 if i % 2 else 1)) // 10 + (n * (2 if i % 2 else 1)) % 10
               for i, n in enumerate(reversed(digits))) % 10 == 0


def register_listing(db: Session, company_id: int, data: ProviderListing, source: SourceSnapshot) -> SecurityListing:
    if data.isin and not valid_isin(data.isin):
        raise ValueError("Invalid ISIN check digit or structure")
    if len(data.mic) != 4 or not data.mic.isalpha() or data.mic != data.mic.upper():
        raise ValueError("MIC must be four uppercase letters")
    if not data.symbol or len(data.symbol) > 30:
        raise ValueError("Invalid listing symbol")
    if data.valid_to is not None and data.valid_to < data.valid_from:
        raise ValueError("Listing end date precedes start date")
    if urlsplit(source.source_url).scheme != "https":
        raise ValueError("Listing provenance must use HTTPS")
    # Never assign the same ISIN to distinct companies.
    security = None
    if data.isin:
        security = db.scalar(select(Security).where(Security.isin == data.isin))
        if security and security.company_id != company_id:
            raise ValueError("ISIN already belongs to a different issuer")
    if security is None:
        security = Security(
            company_id=company_id, security_type=data.security_type,
            share_class=data.share_class, isin=data.isin,
            isin_verified=bool(data.isin), identifier_source=source.provider if data.isin else None,
            identifier_source_url=source.source_url if data.isin else None,
            verified_at=source.retrieved_at if data.isin else None,
        )
        db.add(security)
        db.flush()
    old = list(db.scalars(select(SecurityListing).where(
        SecurityListing.mic == data.mic, SecurityListing.symbol == data.symbol,
        SecurityListing.valid_from <= (data.valid_to or date.max),
        or_(SecurityListing.valid_to.is_(None), SecurityListing.valid_to >= data.valid_from),
    )))
    for listing in old:
        if listing.security_id != security.id:
            raise ValueError("Conflicting exchange symbol and validity interval")
        if (listing.valid_from, listing.valid_to) == (data.valid_from, data.valid_to):
            if listing.currency_code != data.currency:
                raise ValueError("Listing currency conflict")
            return listing
        raise ValueError("Overlapping listing history must be explicitly reconciled")
    row = SecurityListing(
        security_id=security.id, mic=data.mic, symbol=data.symbol,
        currency_code=data.currency, is_adr=data.is_adr,
        valid_from=data.valid_from, valid_to=data.valid_to,
        source_snapshot_id=source.id, verified=True,
    )
    db.add(row)
    db.flush()
    return row
