from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.modules.companies import repository
from app.modules.companies.schemas import CompanyOut, FinancialOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(
    q: str | None = Query(default=None),
    country_id: int | None = Query(default=None),
    sector_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return repository.search_companies(db, q, country_id, sector_id)


@router.get("/search", response_model=list[CompanyOut])
def search_companies(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    return repository.search_companies(db, q, None, None)


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = repository.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/{company_id}/financials", response_model=list[FinancialOut])
def get_company_financials(company_id: int, db: Session = Depends(get_db)):
    return repository.get_company_financials(db, company_id)
