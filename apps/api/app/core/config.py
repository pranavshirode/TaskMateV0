from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Public, committed value: acceptable only for local development and tests.
DEV_SECRET_KEY = "taskmate-dev-secret-key-change-in-production"
INSECURE_ENVIRONMENTS = {"development", "testing"}


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "TaskMate API"
    APP_VERSION: str = "1.0.0"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LOG_LEVEL: str = "INFO"
    # Logs every SQL statement *with parameters* (i.e. client data). Opt-in only.
    SQL_ECHO: bool = False
    SECRET_KEY: str = DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Configuration
    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str = ""
    AI_BASE_URL: str | None = None
    AI_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 2
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 2048
    AI_RATE_LIMIT_PER_MINUTE: int = 30

    # Agent Configuration
    AGENT_MAX_STEPS: int = 10
    AGENT_MAX_TOOL_CALLS: int = 10
    AGENT_MAX_EXECUTION_TIME: int = 120  # seconds
    AGENT_REQUIRE_APPROVAL_FOR_WRITES: bool = True

    # GitHub Integration
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/settings/integrations/github/callback"
    GITHUB_ENCRYPTION_KEY: str = ""  # Fernet key for encrypting tokens

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def validate_settings(settings: Settings) -> None:
    """Refuse to run outside development/testing with insecure defaults."""
    if settings.APP_ENV not in INSECURE_ENVIRONMENTS and settings.SECRET_KEY == DEV_SECRET_KEY:
        raise RuntimeError(
            f"SECRET_KEY is the public development default but APP_ENV={settings.APP_ENV!r}. "
            "Set SECRET_KEY to a random value (e.g. `openssl rand -hex 32`)."
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
