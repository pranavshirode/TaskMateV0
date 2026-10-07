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
    SECRET_KEY: str = "development-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # AI Provider Configuration
    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str = ""  # Required for AI features
    AI_BASE_URL: str | None = None
    AI_TIMEOUT: int = 30  # seconds
    AI_MAX_RETRIES: int = 3
    AI_TEMPERATURE: float = 0.1  # Low temperature for structured outputs
    AI_MAX_TOKENS: int = 2000
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
