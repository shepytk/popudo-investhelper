from sqlalchemy.orm import Session

from app.models import Country

COUNTRIES = [
    ("United States", "USA", "USD", "North America"),
    ("Netherlands", "NLD", "EUR", "Europe"),
    ("Germany", "DEU", "EUR", "Europe"),
    ("South Africa", "ZAF", "ZAR", "Africa"),
    ("United Kingdom", "GBR", "GBP", "Europe"),
]


def seed_countries(db: Session) -> None:
    existing = {country.iso_code for country in db.query(Country).all()}
    for name, iso, currency, region in COUNTRIES:
        if iso in existing:
            continue
        db.add(Country(name=name, iso_code=iso, currency_code=currency, region=region))
    db.flush()
