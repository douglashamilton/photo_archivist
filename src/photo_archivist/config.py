from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "photo-archivist"
    VERSION: str = "0.1.0"
    PORT: int = 8787
    ENV: str = "dev"
    # Path to the SQLite database file. Use an explicit filename by default so the app
    # can create a local DB in the project working directory during development.
    DB_PATH: Path = Path("photo_archivist.db")
    AUTH_CACHE_PATH: Path = Path(".photo_archivist") / "msal_cache.enc"
    MSAL_CLIENT_ID: str = ""
    MSAL_TENANT_ID: str = "common"
    MSAL_SCOPES: list[str] = ["Files.Read"]


settings = Settings()
