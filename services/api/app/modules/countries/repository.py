from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Country, Sector


def list_countries(db: Session) -> list[Country]:
    return list(db.scalars(select(Country).order_by(Country.name)))


def get_country_sectors(db: Session, country_id: int) -> list[Sector]:
    query = (
        select(Sector)
        .join(Company, Company.sector_id == Sector.id)
        .where(Company.country_id == country_id)
        .distinct()
        .order_by(Sector.name)
    )
    return list(db.scalars(query))
