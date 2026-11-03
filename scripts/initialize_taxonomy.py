"""Explicit reference-taxonomy loader; never imports financial statement fixtures."""
from app.shared.database.session import SessionLocal
from scripts.seed_countries import seed_countries
from scripts.seed_sectors import seed_sectors


if __name__ == "__main__":
    with SessionLocal.begin() as db:
        seed_countries(db)
        seed_sectors(db)
    print("Reference countries and sectors initialized")
