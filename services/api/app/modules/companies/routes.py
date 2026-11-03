from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.modules.companies import repository
from app.modules.companies.errors import domain_error
from app.modules.companies.schemas import CompanyOut, CompanyPageOut, FinancialOut
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(
    q: str | None = Query(default=None, max_length=100),
    country_id: int | None = Query(default=None, ge=1),
    sector_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return repository.search_companies(db, q, country_id, sector_id, limit, offset)


@router.get("/search", response_model=list[CompanyOut])
def search_companies(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return repository.search_companies(db, q, None, None, limit, offset)


@router.get("/page", response_model=CompanyPageOut)
def page_companies(
    q: str | None = Query(default=None, max_length=100),
    country_id: int | None = Query(default=None, ge=1),
    sector_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items = repository.search_companies(db, q, country_id, sector_id, limit, offset)
    return CompanyPageOut(
        items=items, total=repository.count_companies(db, q, country_id, sector_id),
        limit=limit, offset=offset,
    )


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = repository.get_company(db, company_id)
    if not company:
        raise domain_error(404, "company_not_found", "Company not found")
    return company


@router.get("/{company_id}/financials", response_model=list[FinancialOut])
def get_company_financials(company_id: int, db: Session = Depends(get_db)):
    if not repository.get_company(db, company_id):
        raise HTTPException(status_code=404, detail={"code": "company_not_found", "message": "Company not found"})
    return repository.get_company_financials(db, company_id)
