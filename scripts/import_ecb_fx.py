"""Explicit operator/scheduler command; reference FX only, not trade execution."""
import os

from app.modules.ingestion.ecb_fx import download_ecb_reference_rates, import_ecb_fx
from app.modules.ingestion.storage import FileSnapshotStore, S3SnapshotStore
from app.shared.database.session import SessionLocal


def main():
    if os.getenv("INVESTHELPER_S3_BUCKET"):
        store = S3SnapshotStore(
            os.environ["INVESTHELPER_S3_BUCKET"],
            os.getenv("INVESTHELPER_S3_ENDPOINT"),
        )
    elif os.getenv("INVESTHELPER_ENV", "production") in {"test", "development"}:
        store = FileSnapshotStore(os.getenv("INVESTHELPER_SNAPSHOT_DIR", "./data/snapshots"))
    else:
        raise RuntimeError("Production source ingestion requires configured object storage")
    batch = download_ecb_reference_rates()
    with SessionLocal.begin() as db:
        count = import_ecb_fx(db, batch, store)
    print(f"Imported {count} new ECB reference FX observations")


if __name__ == "__main__":
    main()
