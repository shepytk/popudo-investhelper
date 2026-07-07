from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.countries import repository
from app.modules.countries.schemas import CountryOut
from app.modules.sectors.schemas import SectorOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/countries", tags=["countries"])


@router.get("", response_model=list[CountryOut])
def get_countries(db: Session = Depends(get_db)):
    return repository.list_countries(db)


@router.get("/{country_id}/sectors", response_model=list[SectorOut])
def get_country_sectors(country_id: int, db: Session = Depends(get_db)):
    return repository.get_country_sectors(db, country_id)
