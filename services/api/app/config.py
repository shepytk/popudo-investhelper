"""Runtime configuration with fail-closed production deployment checks."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fundamental Investment Intelligence Platform API"
    env: str = "production"
    database_url: str = "sqlite:///./investhelper.db"
    sec_user_agent: str = ""
    s3_bucket: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVESTHELPER_")

    @model_validator(mode="after")
    def protect_production(self):
        environment = self.env.lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError("INVESTHELPER_ENV must be development, test or production")
        if environment == "production":
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
                raise ValueError("Production requires PostgreSQL, not a local SQLite database")
            from sqlalchemy.engine import make_url
            parsed = make_url(self.database_url)
            password = parsed.password or ""
            if len(password) < 16 or password.lower() in {
                "investhelper", "postgres", "password", "changeme",
                "admin", "minio123", "replace_with_a_long_random_password",
            }:
                raise ValueError("Production database password is missing or insecure")
        return self


settings = Settings()
