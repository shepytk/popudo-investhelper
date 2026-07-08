from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Sector


def list_sectors(db: Session) -> list[Sector]:
    return list(db.scalars(select(Sector).order_by(Sector.name)))


def get_sector_companies(db: Session, sector_id: int) -> list[Company]:
    return list(db.scalars(select(Company).where(Company.sector_id == sector_id).order_by(Company.name)))
