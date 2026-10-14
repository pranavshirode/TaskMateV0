"""AI Provider initialization and factory."""

from __future__ import annotations

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import get_settings


def get_ai_provider(provider_type: str | None = None) -> BaseAIProvider:
    """Return the configured AI provider.

    Defaults to OpenAIProvider if AI_API_KEY is configured and AI_PROVIDER is 'openai'.
    Falls back to MockAIProvider if no key is configured or for offline/testing.
    """
    settings = get_settings()
    name = (provider_type or settings.AI_PROVIDER).lower()

    if name == "mock":
        return MockAIProvider()

    if name in ("local", "ollama", "lmstudio", "vllm"):
        base_url = settings.AI_BASE_URL or (
            "http://localhost:1234/v1" if name == "lmstudio" else "http://localhost:11434/v1"
        )
        api_key = settings.AI_API_KEY or "local-key"
        return OpenAIProvider(api_key=api_key, model=settings.AI_MODEL, base_url=base_url)

    if name == "openai":
        if settings.AI_API_KEY:
            return OpenAIProvider()
        return MockAIProvider()

    return MockAIProvider()
