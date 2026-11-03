"""Operational queue visibility without exposing admin endpoints publicly."""
import argparse
from sqlalchemy import func, select

from app.models import IngestionJob
from app.shared.database.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    limit = max(1, min(args.limit, 100))
    with SessionLocal() as db:
        totals = db.execute(select(IngestionJob.state, func.count()).group_by(IngestionJob.state)).all()
        print("Job states:", ", ".join(f"{state}={count}" for state, count in totals))
        jobs = db.scalars(select(IngestionJob)
            .order_by(IngestionJob.created_at.desc(), IngestionJob.id.desc())
            .limit(limit))
        for job in jobs:
            print(f"#{job.id} {job.provider}:{job.subject} company={job.company_id} "
                  f"state={job.state} attempts={job.attempts} next={job.next_run_at} "
                  f"error={(job.last_error or '')[:120]}")


if __name__ == "__main__":
    main()
