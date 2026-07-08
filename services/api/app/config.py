from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fundamental Investment Intelligence Platform API"
    database_url: str = "sqlite:///./investhelper.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVESTHELPER_")


settings = Settings()
