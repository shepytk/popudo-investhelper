from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.companies.schemas import CompanyOut
from app.modules.sectors import repository
from app.modules.sectors.schemas import SectorOut, SectorWithCompaniesOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("", response_model=list[SectorOut])
def get_sectors(db: Session = Depends(get_db)):
    return repository.list_sectors(db)


@router.get("/with-companies", response_model=list[SectorWithCompaniesOut])
def get_sectors_with_companies(db: Session = Depends(get_db)):
    sectors = repository.list_sectors(db)
    return [
        {
            "id": sector.id,
            "name": sector.name,
            "description": sector.description,
            "companies": [
                {"id": company.id, "name": company.name, "ticker": company.ticker}
                for company in repository.get_sector_companies(db, sector.id)
            ],
        }
        for sector in sectors
    ]


@router.get("/{sector_id}/companies", response_model=list[CompanyOut])
def get_sector_companies(sector_id: int, db: Session = Depends(get_db)):
    return repository.get_sector_companies(db, sector_id)
