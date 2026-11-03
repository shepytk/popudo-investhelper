"""Read-only readiness check; no implicit schema mutation."""
from sqlalchemy import text
from sqlalchemy.engine import Engine

REQUIRED_TABLES = (
    "schema_migration",
    "country",
    "sector",
    "industry",
    "company",
    "financial_statement",
    "insight",
    "security",
    "security_listing",
    "source_snapshot",
)


def database_ready(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            inspector = __import__("sqlalchemy").inspect(connection)
            return all(inspector.has_table(name) for name in REQUIRED_TABLES)
    except Exception:
        return False
