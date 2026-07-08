from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Company, FinancialStatement


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_companies(db: Session, query: str | None, country_id: int | None, sector_id: int | None) -> list[Company]:
    stmt = select(Company)
    if query:
        escaped = _escape_like(query.lower())
        pattern = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                Company.name.ilike(pattern, escape="\\"),
                Company.ticker.ilike(pattern, escape="\\"),
            )
        )
    if country_id:
        stmt = stmt.where(Company.country_id == country_id)
    if sector_id:
        stmt = stmt.where(Company.sector_id == sector_id)
    return list(db.scalars(stmt.order_by(Company.name)))


def get_company(db: Session, company_id: int) -> Company | None:
    return db.get(Company, company_id)


def get_company_financials(db: Session, company_id: int) -> list[FinancialStatement]:
    stmt = (
        select(FinancialStatement)
        .where(FinancialStatement.company_id == company_id)
        .order_by(FinancialStatement.fiscal_year.desc())
    )
    return list(db.scalars(stmt))
