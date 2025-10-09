from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "photo-archivist"
    VERSION: str = "0.1.0"
    PORT: int = 8787
    ENV: str = "dev"
    # Path to the SQLite database file. Use an explicit filename by default so the app
    # can create a local DB in the project working directory during development.
    DB_PATH: Path = Path("photo_archivist.db")

    class Config:
        env_file = ".env"


settings = Settings()
