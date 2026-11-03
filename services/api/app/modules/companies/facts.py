"""Point-in-time normalized fundamental facts, never inferred financial statements."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinancialFact, SourceSnapshot


def facts_as_of(
    db: Session, company_id: int, as_of: datetime, *,
    limit: int = 50, offset: int = 0,
) -> list[tuple[FinancialFact, SourceSnapshot]]:
    if as_of.tzinfo is not None:
        as_of = as_of.astimezone(timezone.utc).replace(tzinfo=None)
    query = (
        select(FinancialFact, SourceSnapshot)
        .join(SourceSnapshot, FinancialFact.source_snapshot_id == SourceSnapshot.id)
        .where(FinancialFact.company_id == company_id)
        .where(FinancialFact.reported_at <= as_of)
        .where(SourceSnapshot.retrieved_at <= as_of)
        .order_by(
            FinancialFact.period_end.desc(), FinancialFact.concept.asc(),
            FinancialFact.reported_at.desc(), FinancialFact.id.desc(),
        )
        .limit(limit).offset(offset)
    )
    return list(db.execute(query).all())
