from sqlalchemy.orm import Session

from app.models import Sector

SECTORS = [
    "Semiconductors",
    "Information Technology",
    "Real Estate",
    "Banking / Financials",
    "Energy",
    "Industrials",
    "Consumer Goods",
]


def seed_sectors(db: Session) -> None:
    existing = {sector.name for sector in db.query(Sector).all()}
    for name in SECTORS:
        if name in existing:
            continue
        db.add(Sector(name=name, description=f"{name} sector coverage"))
    db.flush()
