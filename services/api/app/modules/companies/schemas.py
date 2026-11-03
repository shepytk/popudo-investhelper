from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    id: int
    name: str
    ticker: str
    exchange: str
    country_id: int
    sector_id: int
    industry_id: int
    currency_code: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class CompanyPageOut(BaseModel):
    items: list[CompanyOut]
    total: int
    limit: int
    offset: int


class FinancialOut(BaseModel):
    company_id: int
    period_type: str
    fiscal_year: int
    period_end_date: date
    revenue: Decimal
    gross_profit: Decimal
    operating_income: Decimal
    net_income: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    cash_and_equivalents: Decimal
    total_debt: Decimal
    operating_cash_flow: Decimal
    capital_expenditure: Decimal
    free_cash_flow: Decimal
    source: str
    source_url: str | None
    reporting_currency: str | None
    amount_unit: str | None
    published_date: date | None
    retrieved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
