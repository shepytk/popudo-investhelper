"""Explicitly attest a company-to-SEC-CIK mapping using official submissions."""
import argparse
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.models import Company, ExternalIdentifier, SourceSnapshot
from app.modules.ingestion.storage import S3SnapshotStore, FileSnapshotStore, object_key
from app.shared.database.session import SessionLocal


def attest_sec_cik(db, store, company_id: int, cik: str, user_agent: str) -> ExternalIdentifier:
    if not cik.isdigit() or len(cik) > 10:
        raise ValueError("CIK must be numeric and at most 10 digits")
    if not user_agent or "@" not in user_agent:
        raise ValueError("Configured SEC user agent with contact email is required")
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError("Unknown company ID")
    normalized = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{normalized}.json"
    with urlopen(Request(url, headers={"User-Agent": user_agent}), timeout=25) as response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("SEC submissions exceed maximum payload")
    document = json.loads(raw)
    if str(document.get("cik", "")).zfill(10) != normalized:
        raise ValueError("SEC CIK mismatch")
    tickers = {str(t).upper() for t in document.get("tickers", [])}
    if company.ticker.upper() not in tickers:
        raise ValueError("SEC ticker mapping not confirmed; manual review required")
    key, digest = object_key("sec_edgar", raw)
    store.put_if_absent(key, raw, "application/json")
    snapshot = db.scalar(select(SourceSnapshot).where(
        SourceSnapshot.provider == "sec_edgar",
        SourceSnapshot.provider_document_id == f"CIK{normalized}-submissions",
        SourceSnapshot.content_hash == digest,
    ))
    if snapshot is None:
        snapshot = SourceSnapshot(
            provider="sec_edgar", source_url=url,
            provider_document_id=f"CIK{normalized}-submissions",
            content_hash=digest, object_key=key,
            retrieved_at=datetime.now(timezone.utc), content_type="application/json",
        )
        db.add(snapshot)
        db.flush()
    existing = db.scalar(select(ExternalIdentifier).where(
        ExternalIdentifier.provider == "sec_edgar",
        ExternalIdentifier.provider_company_id == normalized,
    ))
    if existing and existing.company_id != company_id:
        raise ValueError("CIK already belongs to another issuer")
    if existing is None:
        existing = ExternalIdentifier(
            company_id=company_id, provider="sec_edgar",
            provider_company_id=normalized,
            source_snapshot_id=snapshot.id,
            verified_at=datetime.now(timezone.utc),
        )
        db.add(existing)
    return existing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", type=int, required=True)
    parser.add_argument("--cik", required=True)
    args = parser.parse_args()
    if os.getenv("INVESTHELPER_S3_BUCKET"):
        store = S3SnapshotStore(os.environ["INVESTHELPER_S3_BUCKET"], os.getenv("INVESTHELPER_S3_ENDPOINT"))
    else:
        store = FileSnapshotStore(os.getenv("INVESTHELPER_SNAPSHOT_DIR", "./data/snapshots"))
    with SessionLocal.begin() as db:
        attest_sec_cik(db, store, args.company_id, args.cik, os.getenv("INVESTHELPER_SEC_USER_AGENT", ""))
    print("Verified SEC CIK mapping stored")


if __name__ == "__main__":
    main()
