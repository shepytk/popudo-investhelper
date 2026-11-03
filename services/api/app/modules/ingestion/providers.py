"""Production provider registry; fixtures are never registered for real runs."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, time, timezone
from decimal import Decimal
from urllib.request import Request, urlopen

from app.modules.ingestion.contracts import Evidence, FinancialDataProvider, ProviderBatch, ProviderFact

# Official SEC XBRL companyfacts API. Explicit CIK input, never infer from ticker.
SEC_CONCEPTS = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "NetIncomeLoss": "net_income",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
    "CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capital_expenditure",
    "LongTermDebtCurrent": "current_debt",
    "LongTermDebtNoncurrent": "long_term_debt",
}


class ProviderUnavailable(RuntimeError):
    pass


class SecCompanyFactsProvider(FinancialDataProvider):
    name = "sec_edgar"

    def __init__(self, user_agent: str):
        if not user_agent or "@" not in user_agent or len(user_agent.strip()) < 10:
            raise ProviderUnavailable("SEC_USER_AGENT must identify an operator and email")
        self.user_agent = user_agent

    def collect(self, subject: str) -> ProviderBatch:
        if not (subject.isdigit() and 1 <= len(subject) <= 10):
            raise ValueError("SEC subject must be an explicitly verified 1-10 digit CIK")
        cik = subject.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        request = Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })
        with urlopen(request, timeout=25) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError("SEC response exceeds configured maximum")
        observed = datetime.now(timezone.utc)
        parsed = json.loads(raw)
        if str(parsed.get("cik", "")).zfill(10) != cik:
            raise ValueError("SEC CIK does not match requested issuer")
        facts = []
        seen = set()
        for taxonomy, concepts in parsed.get("facts", {}).items():
            if taxonomy != "us-gaap":
                continue
            for concept, detail in concepts.items():
                canonical = SEC_CONCEPTS.get(concept)
                if not canonical:
                    continue
                for unit, records in detail.get("units", {}).items():
                    if unit != "USD":
                        continue
                    for entry in records:
                        if entry.get("form") not in {"10-K", "10-Q"}:
                            continue
                        if not all(k in entry for k in ("end", "filed", "fy", "accn", "val")):
                            continue
                        start = date.fromisoformat(entry["start"]) if entry.get("start") else None
                        end = date.fromisoformat(entry["end"])
                        published = date.fromisoformat(entry["filed"])
                        if published > observed.date() or end > published:
                            continue
                        fiscal_year = int(entry["fy"])
                        quarter_name = entry.get("fp")
                        fiscal_quarter = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(quarter_name)
                        period_type = "annual" if entry["form"] == "10-K" else "quarterly"
                        if period_type == "annual":
                            fiscal_quarter = None
                        elif fiscal_quarter is None:
                            continue
                        # Sec may expose overlapping duration observations; retain each
                        # version with a deterministic unique source fact identifier.
                        fact_id = ":".join((entry["accn"], concept, unit, entry.get("start", ""), entry["end"], entry.get("frame", ""), str(entry["val"])))
                        if fact_id in seen:
                            continue
                        seen.add(fact_id)
                        facts.append(ProviderFact(
                            fact_id=fact_id,
                            filing_version=entry["accn"],
                            concept=canonical,
                            raw_value=Decimal(str(entry["val"])),
                            raw_unit="ones",
                            currency="USD",
                            fiscal_year=fiscal_year,
                            fiscal_quarter=fiscal_quarter,
                            period_type=period_type,
                            period_start=start,
                            period_end=end,
                            reported_at=datetime.combine(published, time.min, tzinfo=timezone.utc),
                        ))
        evidence = Evidence(
            provider=self.name,
            document_id=f"CIK{cik}-companyfacts",
            source_url=url,
            published_at=None,
            retrieved_at=observed,
            content_type="application/json",
            raw=raw,
        )
        return ProviderBatch(evidence=evidence, facts=tuple(facts))


def provider_from_environment(name: str) -> FinancialDataProvider:
    if name == "sec_edgar":
        return SecCompanyFactsProvider(os.getenv("INVESTHELPER_SEC_USER_AGENT", ""))
    raise ProviderUnavailable(f"Provider {name!r} is not configured or licensed")
