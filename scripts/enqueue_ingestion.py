"""Schedule one verified issuer for future ingestion; compatible with cron."""
import argparse
from app.modules.ingestion.jobs import enqueue
from app.shared.database.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", type=int, required=True)
    parser.add_argument("--provider", default="sec_edgar")
    parser.add_argument("--subject", required=True, help="Verified provider company identifier, e.g. zero-padded SEC CIK")
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        job = enqueue(db, args.company_id, args.provider, args.subject)
        print(f"Enqueued job {job.id} state={job.state}")


if __name__ == "__main__":
    main()
