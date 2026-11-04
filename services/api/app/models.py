from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
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
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
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

    __table_args__ = (
        Index("ix_company_name_id", "name", "id"),
        Index("ix_company_ticker", "ticker"),
        Index("ix_company_country_sector", "country_id", "sector_id"),
    )

    country: Mapped[Country] = relationship()
    sector: Mapped[Sector] = relationship()
    industry: Mapped[Industry] = relationship()


class FinancialStatement(Base):
    __tablename__ = "financial_statement"
    __table_args__ = (Index("ix_statement_company_period", "company_id", "period_end_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(12), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    operating_income: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    net_income: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_equity: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    cash_and_equivalents: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_debt: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    operating_cash_flow: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    capital_expenditure: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    free_cash_flow: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    source_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("source_snapshot.id"), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporting_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    amount_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Insight(Base):
    __tablename__ = "insight"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance_sheet_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[str] = mapped_column(Text, nullable=False)
    opportunities: Mapped[str] = mapped_column(Text, nullable=False)
    questions_for_further_research: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    analysis_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
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


class ValuationMetric(Base):
    __tablename__ = "valuation_metric"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    enterprise_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    forward_pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_to_book: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_to_sales: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    ev_to_ebitda: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    free_cash_flow_yield: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class MarketPrice(Base):
    __tablename__ = "market_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    high: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    low: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    close: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class CompanyDocument(Base):
    __tablename__ = "company_document"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)
    extracted_text_path: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class WatchlistItem(Base):
    __tablename__ = "watchlist_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlist.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Security(Base):
    """Issuer/company may have multiple share classes and instruments."""
    __tablename__ = "security"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    security_type: Mapped[str] = mapped_column(String(20), nullable=False)
    share_class: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    isin_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    identifier_source: Mapped[str | None] = mapped_column(String(120))
    identifier_source_url: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    __table_args__ = (
        Index("ix_security_company", "company_id"),
        CheckConstraint("isin_verified = false OR (isin IS NOT NULL AND identifier_source IS NOT NULL AND identifier_source_url IS NOT NULL AND verified_at IS NOT NULL)", name="ck_security_verified_evidence"),
    )


class SecurityListing(Base):
    """Symbol scope is exchange+date, never globally unique."""
    __tablename__ = "security_listing"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), nullable=False)
    mic: Mapped[str] = mapped_column(String(4), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    is_adr: Mapped[bool] = mapped_column(default=False, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    source_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("source_snapshot.id"))
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    __table_args__ = (
        UniqueConstraint("mic", "symbol", "valid_from", name="uq_listing_mic_symbol_from"),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_listing_dates"),
        CheckConstraint("verified = false OR source_snapshot_id IS NOT NULL", name="ck_listing_source"),
        Index("ix_listing_symbol_mic", "symbol", "mic"),
    )


class SymbolAlias(Base):
    __tablename__ = "symbol_alias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("security_listing.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    source_snapshot_id: Mapped[int] = mapped_column(ForeignKey("source_snapshot.id"), nullable=False)
    __table_args__ = (UniqueConstraint("listing_id", "symbol", "valid_from", name="uq_symbol_alias"),)


class SourceSnapshot(Base):
    """Immutable source payload content address; stored bytes live in object storage."""
    __tablename__ = "source_snapshot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    provider_document_id: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (
        UniqueConstraint("provider", "provider_document_id", "content_hash", name="uq_source_content_version"),
        Index("ix_snapshot_provider_date", "provider", "retrieved_at"),
    )


class FinancialFact(Base):
    __tablename__ = "financial_fact"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    source_snapshot_id: Mapped[int] = mapped_column(ForeignKey("source_snapshot.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_fact_id: Mapped[str] = mapped_column(String(255), nullable=False)
    filing_version: Mapped[str] = mapped_column(String(80), nullable=False)
    concept: Mapped[str] = mapped_column(String(100), nullable=False)
    period_type: Mapped[str] = mapped_column(String(12), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int | None] = mapped_column(Integer)
    raw_value: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    raw_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_value: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    __table_args__ = (
        UniqueConstraint("company_id", "provider", "provider_fact_id", "filing_version", name="uq_fact_provider_version"),
        Index("ix_fact_company_period", "company_id", "concept", "period_end"),
    )


class QuoteObservation(Base):
    __tablename__ = "quote_observation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("security_listing.id"), nullable=False)
    source_snapshot_id: Mapped[int] = mapped_column(ForeignKey("source_snapshot.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    revision: Mapped[str] = mapped_column(String(80), nullable=False, default="original")
    close: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    __table_args__ = (UniqueConstraint("listing_id", "provider", "session_date", "revision", name="uq_quote_version"),)


class FxObservation(Base):
    __tablename__ = "fx_observation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_snapshot_id: Mapped[int] = mapped_column(ForeignKey("source_snapshot.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    observed_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    revision: Mapped[str] = mapped_column(String(80), nullable=False, default="original")
    __table_args__ = (
        UniqueConstraint("provider", "observed_date", "base_currency", "quote_currency", "revision", name="uq_fx_observation"),
        CheckConstraint("rate > 0", name="ck_fx_positive_rate"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_job"
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_error: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    __table_args__ = (Index("ix_ingestion_queue", "state", "next_run_at"),)


class ExternalIdentifier(Base):
    """Attested provider identifier, e.g. SEC CIK, tied to a known issuer."""
    __tablename__ = "external_identifier"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_company_id: Mapped[str] = mapped_column(String(80), nullable=False)
    source_snapshot_id: Mapped[int] = mapped_column(ForeignKey("source_snapshot.id"), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    __table_args__ = (
        UniqueConstraint("provider", "provider_company_id", name="uq_external_provider_id"),
        UniqueConstraint("company_id", "provider", name="uq_company_provider"),
    )


class ScreeningPreset(Base):
    """A durable saved screening query, isolated by the authenticated user."""
    __tablename__ = "screening_preset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_screening_preset_owner_name"),
        Index("ix_screening_preset_owner_id", "user_id", "id"),
    )
