from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "photo-archivist"
    VERSION: str = "0.1.0"
    PORT: int = 8787
    ENV: str = "dev"

    class Config:
        env_file = ".env"


settings = Settings()
