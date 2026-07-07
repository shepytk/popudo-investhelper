from datetime import date

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


class FinancialOut(BaseModel):
    company_id: int
    period_type: str
    fiscal_year: int
    period_end_date: date
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    total_assets: float
    total_liabilities: float
    total_equity: float
    cash_and_equivalents: float
    total_debt: float
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    source: str

    model_config = ConfigDict(from_attributes=True)
