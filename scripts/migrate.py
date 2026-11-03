"""Transactional PostgreSQL migrations, with checksums and an advisory lock.

Run explicitly before starting the API. Never mutate schema on API import.
The first migration is idempotent for legacy installations that ran SQL by hand.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "infra" / "migrations"
LOCK_ID = 26031103


def apply_migrations(url: str, directory: Path = MIGRATIONS) -> list[str]:
    if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise ValueError("Versioned production migrations require PostgreSQL")
    engine = create_engine(url, future=True)
    applied: list[str] = []
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:lock)"), {"lock": LOCK_ID})
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migration (
                    filename TEXT PRIMARY KEY,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """))
            found = {row.filename: row.checksum for row in connection.execute(text("SELECT filename, checksum FROM schema_migration"))}
            scripts = sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql"))
            if not scripts:
                raise RuntimeError("No schema migrations found")
            expected = {s.name for s in scripts}
            unexpected = set(found) - expected
            if unexpected:
                raise RuntimeError(f"Missing historical migrations: {sorted(unexpected)}")
            for script in scripts:
                sql = script.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
                if script.name in found:
                    if found[script.name] != checksum:
                        raise RuntimeError(f"Migration checksum changed: {script.name}")
                    continue
                connection.exec_driver_sql(sql)
                connection.execute(
                    text("INSERT INTO schema_migration(filename, checksum) VALUES (:f, :c)"),
                    {"f": script.name, "c": checksum},
                )
                applied.append(script.name)
    finally:
        engine.dispose()
    return applied


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply database migrations")
    parser.add_argument("--database-url", default=os.getenv("INVESTHELPER_DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or INVESTHELPER_DATABASE_URL is required")
    for filename in apply_migrations(args.database_url):
        print(f"Applied {filename}")
    print("Schema up to date")


if __name__ == "__main__":
    main()
