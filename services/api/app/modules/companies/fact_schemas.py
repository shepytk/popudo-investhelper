from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SourcedFactOut(BaseModel):
    id: int
    concept: str
    period_type: str
    period_start: date | None
    period_end: date
    fiscal_year: int
    fiscal_quarter: int | None
    value: Decimal
    currency_code: str
    provider: str
    filing_version: str
    source_url: str
    published_at: datetime
    retrieved_at: datetime
    source_sha256: str


class FactPageOut(BaseModel):
    items: list[SourcedFactOut]
    limit: int
    offset: int
    as_of: datetime


class SourcedQuoteOut(BaseModel):
    listing_id: int
    mic: str
    symbol: str
    date: date
    close: Decimal
    currency_code: str
    provider: str
    source_url: str
    source_sha256: str
    retrieved_at: datetime
