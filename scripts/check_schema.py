"""Verify production PostgreSQL schema against ORM tables and constraints."""
import os
from collections import Counter

from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, inspect

from app.models import Base


def check_schema(database_url: str) -> list[str]:
    engine = create_engine(database_url, future=True)
    errors = []
    try:
        inspector = inspect(engine)
        for name, model_table in Base.metadata.tables.items():
            if not inspector.has_table(name):
                errors.append(f"missing table: {name}")
                continue
            reflected = {x["name"]: x for x in inspector.get_columns(name)}
            for col in model_table.columns:
                if col.name not in reflected:
                    errors.append(f"missing column: {name}.{col.name}")
                    continue
                got = reflected[col.name]
                if bool(got["nullable"]) != bool(col.nullable):
                    errors.append(f"nullability mismatch: {name}.{col.name}")
                expected = col.type
                actual = got["type"]
                if hasattr(expected, "length") and expected.length is not None:
                    if getattr(actual, "length", None) != expected.length:
                        errors.append(f"varchar length mismatch: {name}.{col.name}")
                if hasattr(expected, "precision") and expected.precision is not None:
                    if (getattr(actual, "precision", None), getattr(actual, "scale", None)) != (expected.precision, expected.scale):
                        errors.append(f"numeric precision mismatch: {name}.{col.name}")
            expected_indexes = {idx.name for idx in model_table.indexes}
            actual_indexes = {idx["name"] for idx in inspector.get_indexes(name)}
            for missing in expected_indexes - actual_indexes:
                errors.append(f"missing index: {missing}")
            uniques = {tuple(sorted(x["column_names"])) for x in inspector.get_unique_constraints(name)}
            for constraint in model_table.constraints:
                if isinstance(constraint, UniqueConstraint):
                    columns = tuple(sorted(col.name for col in constraint.columns))
                    if columns not in uniques:
                        errors.append(f"missing unique constraint: {name} {columns}")
                if isinstance(constraint, CheckConstraint) and constraint.name:
                    checks = {c["name"] for c in inspector.get_check_constraints(name)}
                    if constraint.name not in checks:
                        errors.append(f"missing check constraint: {constraint.name}")
    finally:
        engine.dispose()
    return errors


if __name__ == "__main__":
    url = os.getenv("INVESTHELPER_DATABASE_URL")
    if not url:
        raise SystemExit("INVESTHELPER_DATABASE_URL required")
    failures = check_schema(url)
    if failures:
        raise SystemExit("\n".join(failures))
    print("ORM schema matches PostgreSQL migration state")
