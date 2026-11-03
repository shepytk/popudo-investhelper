from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialStatement
from app.modules.companies.verification import verified_statements


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _filters(query: str | None, country_id: int | None, sector_id: int | None):
    conditions = []
    if query:
        escaped = _escape_like(query.strip())
        pattern = f"%{escaped}%"
        conditions.append(or_(
            Company.name.ilike(pattern, escape="\\"),
            Company.ticker.ilike(pattern, escape="\\"),
        ))
    if country_id is not None:
        conditions.append(Company.country_id == country_id)
    if sector_id is not None:
        conditions.append(Company.sector_id == sector_id)
    return conditions


def search_companies(
    db: Session,
    query: str | None,
    country_id: int | None,
    sector_id: int | None,
    limit: int = 50,
    offset: int = 0,
) -> list[Company]:
    conditions = _filters(query, country_id, sector_id)
    stmt = (
        select(Company)
        .where(*conditions)
        .order_by(Company.name.asc(), Company.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


def count_companies(db: Session, query: str | None, country_id: int | None, sector_id: int | None) -> int:
    return db.scalar(select(func.count()).select_from(Company).where(*_filters(query, country_id, sector_id))) or 0


def get_company(db: Session, company_id: int) -> Company | None:
    return db.get(Company, company_id)


def get_company_financials(db: Session, company_id: int) -> list[FinancialStatement]:
    stmt = (
        select(FinancialStatement)
        .where(FinancialStatement.company_id == company_id)
        .order_by(FinancialStatement.period_end_date.desc(), FinancialStatement.id.desc())
        .limit(100)
    )
    return verified_statements(list(db.scalars(stmt)))
