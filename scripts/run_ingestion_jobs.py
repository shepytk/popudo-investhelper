"""Scheduled ingestion worker. Invocation is explicit; no request-path fetching."""
import argparse
import os
import time

from app.modules.ingestion.jobs import work_one
from app.modules.ingestion.storage import FileSnapshotStore, S3SnapshotStore
from app.shared.database.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=30)
    args = parser.parse_args()
    if os.getenv("INVESTHELPER_S3_BUCKET"):
        store = S3SnapshotStore(os.environ["INVESTHELPER_S3_BUCKET"], os.getenv("INVESTHELPER_S3_ENDPOINT"))
    else:
        if os.getenv("INVESTHELPER_ENV", "production") not in {"test", "development"}:
            raise RuntimeError("Production ingestion requires configured immutable S3/MinIO storage")
        store = FileSnapshotStore(os.getenv("INVESTHELPER_SNAPSHOT_DIR", "./data/snapshots"))
    while True:
        active = work_one(SessionLocal, store)
        if args.once:
            break
        if not active:
            time.sleep(max(5, args.interval_seconds))


if __name__ == "__main__":
    main()
