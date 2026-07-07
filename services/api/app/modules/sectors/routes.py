from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.companies.schemas import CompanyOut
from app.modules.sectors import repository
from app.modules.sectors.schemas import SectorOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("", response_model=list[SectorOut])
def get_sectors(db: Session = Depends(get_db)):
    return repository.list_sectors(db)


@router.get("/{sector_id}/companies", response_model=list[CompanyOut])
def get_sector_companies(sector_id: int, db: Session = Depends(get_db)):
    return repository.get_sector_companies(db, sector_id)
