from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    iso_code: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    region: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Sector(Base):
    __tablename__ = "sector"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Industry(Base):
    __tablename__ = "industry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sector.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    isin: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    exchange: Mapped[str] = mapped_column(String(120), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("country.id"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sector.id"), nullable=False)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industry.id"), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    website_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    investor_relations_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    country: Mapped[Country] = relationship()
    sector: Mapped[Sector] = relationship()
    industry: Mapped[Industry] = relationship()


class FinancialStatement(Base):
    __tablename__ = "financial_statement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(12), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    gross_profit: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    operating_income: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    net_income: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    total_assets: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    total_liabilities: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    total_equity: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    cash_and_equivalents: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    total_debt: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    operating_cash_flow: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    capital_expenditure: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    free_cash_flow: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Insight(Base):
    __tablename__ = "insight"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    growth_score: Mapped[float] = mapped_column(Float, nullable=False)
    valuation_score: Mapped[float] = mapped_column(Float, nullable=False)
    balance_sheet_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[str] = mapped_column(Text, nullable=False)
    opportunities: Mapped[str] = mapped_column(Text, nullable=False)
    questions_for_further_research: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class RiskFlag(Base):
    __tablename__ = "risk_flag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    risk_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
