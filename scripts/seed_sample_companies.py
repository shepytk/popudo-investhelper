from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Country, FinancialStatement, Industry, Sector
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


def seed_data(db: Session) -> None:
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
            isin=f"{country_iso}{ticker}0000",
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

        db.add(
            FinancialStatement(
                company_id=company.id,
                period_type="annual",
                fiscal_year=2025,
                fiscal_quarter=4,
                period_end_date=date(2025, 12, 31),
                revenue=100000.0,
                gross_profit=55000.0,
                operating_income=30000.0,
                net_income=24000.0,
                total_assets=180000.0,
                total_liabilities=90000.0,
                total_equity=90000.0,
                cash_and_equivalents=25000.0,
                total_debt=30000.0,
                operating_cash_flow=28000.0,
                capital_expenditure=5000.0,
                free_cash_flow=23000.0,
                source="seed",
            )
        )

    db.commit()


if __name__ == "__main__":
    from app.shared.database.session import SessionLocal

    with SessionLocal() as session:
        seed_data(session)
