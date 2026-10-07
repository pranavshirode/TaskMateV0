"""AI provider factory.

Creates the appropriate AIProvider based on configuration.
Supports future providers without code changes in the application layer.
"""

import logging

from app.ai.errors import AINotConfiguredError
from app.ai.providers.base import AIProvider
from app.core.config import Settings

logger = logging.getLogger(__name__)

_provider_instance: AIProvider | None = None


def create_ai_provider(settings: Settings) -> AIProvider:
    """Create an AI provider from application settings.

    Args:
        settings: Application settings containing AI configuration.

    Returns:
        Configured AIProvider instance.

    Raises:
        AINotConfiguredError: If the provider is not properly configured.
        ValueError: If the provider type is unknown.
    """
    provider_type = settings.AI_PROVIDER.lower()

    if provider_type == "openai":
        from app.ai.providers.openai import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL,
            base_url=settings.AI_BASE_URL,
            timeout=settings.AI_TIMEOUT,
            max_retries=settings.AI_MAX_RETRIES,
            default_temperature=settings.AI_TEMPERATURE,
            default_max_tokens=settings.AI_MAX_TOKENS,
        )
    else:
        raise ValueError(
            f"Unknown AI provider: {provider_type}. "
            f"Supported providers: openai"
        )


def get_ai_provider(settings: Settings) -> AIProvider:
    """Get or create the singleton AI provider.

    Uses a module-level singleton to avoid creating multiple
    client instances.
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = create_ai_provider(settings)
        logger.info(
            "AI provider initialized",
            extra={
                "provider": settings.AI_PROVIDER,
                "model": settings.AI_MODEL,
            },
        )
    return _provider_instance


def reset_ai_provider() -> None:
    """Reset the singleton provider. Used for testing."""
    global _provider_instance
    _provider_instance = None
