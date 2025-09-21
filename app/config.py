"""Configuration management for the Photo Archivist application."""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "Photo Archivist"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = False
    secret_key: str = ""  # Must be set in production

    # Database
    database_url: str = "sqlite+aiosqlite:///./photo_archive.db"

    # MSAL Auth
    msal_client_id: str = ""  # Must be set in production
    msal_client_secret: str = ""  # Must be set in production
    msal_tenant_id: str = ""  # Must be set in production
    msal_authority: str = "https://login.microsoftonline.com/{tenant_id}"
    msal_redirect_path: str = "/auth/callback"

    # OneDrive Graph API
    graph_api_version: str = "v1.0"
    graph_photo_folder_id: str = ""  # Must be set in production
    graph_scopes: List[str] = ["Files.Read", "offline_access"]

    # Kite Print API
    kite_api_key: str = ""  # Must be set in production
    kite_api_secret: str = ""  # Must be set in production
    kite_test_mode: bool = True
    kite_api_base_url: str = "https://api.kite.ly/v4.0"

    # Sync settings
    sync_interval_minutes: int = 1440  # Monthly by default
    max_retries: int = 3
    backoff_factor: int = 2
    max_photos_per_page: int = 200

    # Scoring settings
    shortlist_size: int = 20
    dupe_threshold: int = 5  # pHash Hamming distance
    min_sharpness_score: float = 0.5
    min_exposure_score: float = 0.5

    # Security
    cookie_max_age: int = 3600  # 1 hour
    cookie_name: str = "photo_archivist_session"
    encryption_key: str = ""  # Must be set in production

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "photo_archivist.log"

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "PA_"  # Photo Archivist environment prefix


def get_settings() -> Settings:
    """Get application settings, with test overrides if present."""
    import os
    if os.getenv("PYTEST_CURRENT_TEST"):
        # Test environment - use stub values
        return Settings(
            secret_key="test-secret-key-32-chars-exactly!!",
            msal_client_id="test-client-id",
            msal_client_secret="test-client-secret",
            msal_tenant_id="test-tenant-id",
            graph_photo_folder_id="test-folder-id",
            kite_api_key="test-kite-key",
            kite_api_secret="test-kite-secret",
            encryption_key="test-encryption-key-32-chars!!!!",
            database_url="sqlite+aiosqlite://",
            debug=True
        )
    return Settings()


# Global settings instance
settings = get_settings()