"""Provider contracts. Domain and API modules do not depend on HTTP or MinIO."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Evidence:
    provider: str
    document_id: str
    source_url: str
    published_at: datetime | None
    retrieved_at: datetime
    content_type: str
    raw: bytes


@dataclass(frozen=True)
class ProviderFact:
    fact_id: str
    filing_version: str
    concept: str
    raw_value: Decimal
    raw_unit: str
    currency: str
    fiscal_year: int
    fiscal_quarter: int | None
    period_type: str
    period_start: date | None
    period_end: date
    reported_at: datetime


@dataclass(frozen=True)
class ProviderListing:
    security_type: str
    share_class: str
    isin: str | None
    mic: str
    symbol: str
    currency: str
    is_adr: bool
    valid_from: date
    valid_to: date | None = None


@dataclass(frozen=True)
class ProviderQuote:
    listing_id: int
    session_date: date
    close: Decimal
    currency: str
    revision: str = "original"


@dataclass(frozen=True)
class ProviderFX:
    observed_date: date
    base_currency: str
    quote_currency: str
    rate: Decimal
    revision: str = "original"


@dataclass(frozen=True)
class ProviderBatch:
    evidence: Evidence
    facts: tuple[ProviderFact, ...] = ()
    listings: tuple[ProviderListing, ...] = ()
    quotes: tuple[ProviderQuote, ...] = ()
    fx_rates: tuple[ProviderFX, ...] = ()


class FinancialDataProvider(Protocol):
    name: str

    def collect(self, subject: str) -> ProviderBatch:
        """Fetch a bounded, auditable batch; never write to the database."""
        ...


class SnapshotStore(Protocol):
    def put_if_absent(self, key: str, data: bytes, content_type: str) -> None:
        """Immutable write; fail if existing bytes differ."""
        ...

    def get(self, key: str) -> bytes:
        """Retrieve exactly the bytes for this content-addressed key."""
        ...


@dataclass(frozen=True)
class ProviderCorporateAction:
    """Optional vendor-neutral split, dividend or merger record."""
    listing_id: int
    action_id: str
    action_type: str
    effective_date: date
    amount: Decimal | None = None
    currency: str | None = None


@dataclass(frozen=True)
class ProviderEstimate:
    """Source-identified forward estimate; never treat as reported earnings."""
    listing_id: int
    estimate_id: str
    metric: str
    period_end: date
    value: Decimal
    currency: str
    published_at: datetime


class CorporateActionProvider(Protocol):
    name: str

    def collect_actions(self, listing_id: int) -> tuple[Evidence, tuple[ProviderCorporateAction, ...]]:
        ...


class ConsensusEstimateProvider(Protocol):
    name: str

    def collect_estimates(self, listing_id: int) -> tuple[Evidence, tuple[ProviderEstimate, ...]]:
        ...
