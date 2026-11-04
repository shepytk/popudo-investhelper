import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_sqlite_and_weak_credentials():
    with pytest.raises(ValidationError, match="PostgreSQL"):
        Settings(env="production", database_url="sqlite:///./prod.db")
    with pytest.raises(ValidationError, match="insecure"):
        Settings(env="production", database_url="postgresql+psycopg2://user:investhelper@db:5432/app")


def test_production_requires_strong_db_password():
    settings = Settings(
        env="production",
        database_url="postgresql+psycopg2://user:correct-horse-battery-staple@db:5432/app",
    )
    assert settings.env == "production"


def test_explicit_test_environment_can_use_sqlite():
    settings = Settings(env="test", database_url="sqlite:///./tests.db")
    assert settings.env == "test"
