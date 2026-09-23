from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "TaskMate API"
    APP_VERSION: str = "0.1.0"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
