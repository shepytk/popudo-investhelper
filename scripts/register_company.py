"""Operator command to register unverified issuer metadata for later attestation."""
import argparse
from sqlalchemy import select

from app.models import Company, Country, Industry, Sector
from app.modules.companies.normalization import normalize_currency
from app.shared.database.session import SessionLocal


def register(db, *, name: str, ticker: str, exchange: str,
             country_iso: str, sector_name: str, industry_name: str,
             currency: str) -> Company:
    country = db.scalar(select(Country).where(Country.iso_code == country_iso.upper()))
    sector = db.scalar(select(Sector).where(Sector.name == sector_name))
    if not country or not sector:
        raise ValueError("Country and sector must exist; run initialize_taxonomy.py")
    if not all([name.strip(), ticker.strip(), exchange.strip(), industry_name.strip()]):
        raise ValueError("Issuer identity and classification cannot be blank")
    currency = normalize_currency(currency)
    company = db.scalar(select(Company).where(
        Company.name == name.strip(),
        Company.ticker == ticker.upper().strip(),
        Company.exchange == exchange.strip(),
        Company.country_id == country.id,
    ))
    if company:
        return company
    industry = db.scalar(select(Industry).where(
        Industry.sector_id == sector.id,
        Industry.name == industry_name.strip(),
    ))
    if not industry:
        industry = Industry(sector_id=sector.id, name=industry_name.strip(), description="")
        db.add(industry)
        db.flush()
    company = Company(
        name=name.strip(), ticker=ticker.upper().strip(), isin="",
        exchange=exchange.strip(), country_id=country.id,
        sector_id=sector.id, industry_id=industry.id,
        currency_code=currency, website_url="", investor_relations_url="",
        description="",
    )
    db.add(company)
    db.flush()
    return company


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--exchange", required=True)
    parser.add_argument("--country", required=True, help="ISO3 country")
    parser.add_argument("--sector", required=True)
    parser.add_argument("--industry", required=True)
    parser.add_argument("--currency", required=True)
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        company = register(
            db, name=args.name, ticker=args.ticker, exchange=args.exchange,
            country_iso=args.country, sector_name=args.sector,
            industry_name=args.industry, currency=args.currency,
        )
        print(f"Registered unverified company ID {company.id}; verify its provider identity before importing")


if __name__ == "__main__":
    main()
