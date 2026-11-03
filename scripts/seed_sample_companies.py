import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Country, Industry, Sector
from scripts.seed_countries import seed_countries
from scripts.seed_sectors import seed_sectors

COMPANIES = [
    ("ASML", "ASML", "Euronext Amsterdam", "NLD", "Semiconductors", "Semiconductor Equipment"),
    ("Nvidia", "NVDA", "NASDAQ", "USA", "Semiconductors", "Semiconductors"),
    ("AMD", "AMD", "NASDAQ", "USA", "Semiconductors", "Semiconductors"),
    ("TSMC", "TSM", "NYSE", "USA", "Semiconductors", "Semiconductors"),
    ("Intel", "INTC", "NASDAQ", "USA", "Semiconductors", "Semiconductors"),
    ("Shell", "SHEL", "LSE", "GBR", "Energy", "Integrated Energy"),
    ("Adyen", "ADYEN", "Euronext Amsterdam", "NLD", "Banking / Financials", "Payments"),
    ("Prosus", "PRX", "Euronext Amsterdam", "NLD", "Information Technology", "Internet Services"),
    ("Vonovia", "VNA", "XETRA", "DEU", "Real Estate", "Residential REIT"),
    ("SAP", "SAP", "XETRA", "DEU", "Information Technology", "Enterprise Software"),
]


def seed_data(db: Session, *, allow_demo: bool = False) -> None:
    """Explicit development fixture loader. Never called by API startup."""
    if not allow_demo or os.getenv("INVESTHELPER_ENV", "production").lower() not in {"development", "test"}:
        raise RuntimeError("Demo seeding is allowed only with allow_demo=True in development/test")
    seed_countries(db)
    seed_sectors(db)

    countries = {c.iso_code: c for c in db.scalars(select(Country)).all()}
    sectors = {s.name: s for s in db.scalars(select(Sector)).all()}

    existing_tickers = {ticker for ticker, in db.execute(select(Company.ticker)).all()}

    industries_cache: dict[tuple[str, int], Industry] = {}

    for name, ticker, exchange, country_iso, sector_name, industry_name in COMPANIES:
        if ticker in existing_tickers:
            continue

        sector = sectors[sector_name]
        industry_key = (industry_name, sector.id)
        industry = industries_cache.get(industry_key)
        if not industry:
            industry = db.scalar(
                select(Industry).where(Industry.name == industry_name, Industry.sector_id == sector.id)
            )
            if not industry:
                industry = Industry(name=industry_name, sector_id=sector.id, description=industry_name)
                db.add(industry)
                db.flush()
            industries_cache[industry_key] = industry

        company = Company(
            name=name,
            ticker=ticker,
            isin="",  # Unknown, never synthesize an identifier.
            exchange=exchange,
            country_id=countries[country_iso].id,
            sector_id=sector.id,
            industry_id=industry.id,
            currency_code=countries[country_iso].currency_code,
            website_url="",
            investor_relations_url="",
            description=f"{name} is tracked for fundamental investment analysis.",
        )
        db.add(company)
        db.flush()


    db.commit()


if __name__ == "__main__":
    from app.shared.database.session import SessionLocal

    with SessionLocal() as session:
        seed_data(session, allow_demo=True)
