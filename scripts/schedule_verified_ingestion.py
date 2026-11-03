"""Periodic enqueue-only scheduler. Run with cron/Cloud Scheduler, never in API requests."""
import argparse

from sqlalchemy import select

from app.models import ExternalIdentifier
from app.modules.ingestion.jobs import enqueue
from app.shared.database.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="sec_edgar")
    args = parser.parse_args()
    count = 0
    with SessionLocal.begin() as db:
        for identifier in db.scalars(select(ExternalIdentifier).where(
            ExternalIdentifier.provider == args.provider,
        ).order_by(ExternalIdentifier.company_id)):
            enqueue(db, identifier.company_id, identifier.provider, identifier.provider_company_id)
            count += 1
    print(f"Scheduled {count} verified issuers (duplicates reused)")


if __name__ == "__main__":
    main()
