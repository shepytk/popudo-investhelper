"""Deterministic offline adapter for ingestion contract tests.

Fixtures are *never* registered by the production provider factory. The adapter
returns untrusted evidence: the normal import pipeline rejects it.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.modules.ingestion.contracts import (
    Evidence, FinancialDataProvider, ProviderBatch, ProviderFact,
    ProviderListing, ProviderQuote,
)

_FIXTURE_ENVS = frozenset({"test", "development"})


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Fixture timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _amount(value: str) -> Decimal:
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("Fixture values must be finite")
    return result


class FixtureFinancialDataProvider(FinancialDataProvider):
    """Reads a checked-in fixture file without network, database or clock access."""

    name = "fixture"

    def __init__(self, path: str | Path, *, environment: str | None = None):
        env = (environment or os.getenv("INVESTHELPER_ENV", "production")).lower()
        if env not in _FIXTURE_ENVS:
            raise RuntimeError("Fixture provider is disabled outside development/test")
        self._path = Path(path)

    def collect(self, subject: str) -> ProviderBatch:
        if not subject or "/" in subject or "\\" in subject or ".." in subject:
            raise ValueError("Invalid fixture subject")
        raw = self._path.read_bytes()
        payload = json.loads(raw)
        if payload["subject"] != subject:
            raise ValueError("Fixture subject does not match requested subject")
        observed = _datetime(payload["retrieved_at"])
        if observed > datetime.now(timezone.utc):
            raise ValueError("Future fixture retrieval time")
        evidence = Evidence(
            provider=self.name,
            document_id=payload["document_id"],
            source_url="https://fixtures.invalid/offline/" + subject,
            published_at=_datetime(payload["published_at"]),
            retrieved_at=observed,
            content_type="application/json",
            raw=raw,
        )
        facts = tuple(ProviderFact(
            fact_id=row["fact_id"],
            filing_version=row["filing_version"],
            concept=row["concept"],
            raw_value=_amount(row["raw_value"]),
            raw_unit=row["raw_unit"],
            currency=row["currency"],
            fiscal_year=int(row["fiscal_year"]),
            fiscal_quarter=row.get("fiscal_quarter"),
            period_type=row["period_type"],
            period_start=_date(row["period_start"]) if row.get("period_start") else None,
            period_end=_date(row["period_end"]),
            reported_at=_datetime(row["reported_at"]),
        ) for row in payload.get("facts", []))
        listings = tuple(ProviderListing(
            security_type=row["security_type"],
            share_class=row["share_class"],
            isin=row.get("isin"),
            mic=row["mic"],
            symbol=row["symbol"],
            currency=row["currency"],
            is_adr=bool(row["is_adr"]),
            valid_from=_date(row["valid_from"]),
            valid_to=_date(row["valid_to"]) if row.get("valid_to") else None,
        ) for row in payload.get("listings", []))
        quotes = tuple(ProviderQuote(
            listing_id=int(row["listing_id"]),
            session_date=_date(row["session_date"]),
            close=_amount(row["close"]),
            currency=row["currency"],
            revision=row.get("revision", "original"),
        ) for row in payload.get("quotes", []))
        return ProviderBatch(evidence=evidence, facts=facts, listings=listings, quotes=quotes)
