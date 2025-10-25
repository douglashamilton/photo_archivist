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
    # Number of photos to keep in each shortlist produced by a scan.
    SCAN_SHORTLIST_SIZE: int = 10
    # Root path to query when traversing OneDrive via the Graph delta API.
    GRAPH_ROOT_PATH: str = "/me/drive/root"
    # Maximum number of items to request per delta page. Microsoft Graph allows up to 200.
    GRAPH_PAGE_SIZE: int = 200


settings = Settings()
