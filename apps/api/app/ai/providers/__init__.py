"""AI Provider initialization and factory."""

from __future__ import annotations

import logging
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.fallback_provider import FallbackAIProvider
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_ai_provider(provider_type: str | None = None) -> BaseAIProvider:
    """Return the configured AI provider.

    Supports Gemini, OpenAI, Ollama, LM Studio, Mock, or a Primary+Fallback setup.
    """
    settings = get_settings()
    name = (provider_type or settings.AI_PROVIDER).lower()

    if name == "mock":
        return MockAIProvider()

    def _create_single_provider(
        p_name: str,
        p_key: str,
        p_model: str,
        p_base_url: str | None,
    ) -> BaseAIProvider:
        p_name = p_name.lower()
        if p_name in ("gemini", "google"):
            base_url = (
                p_base_url
                or "https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            model = p_model or "gemini-flash-latest"
            return OpenAIProvider(
                api_key=p_key,
                model=model,
                base_url=base_url,
            )

        if p_name in ("local", "ollama", "lmstudio", "vllm"):
            base_url = p_base_url or (
                "http://localhost:1234/v1"
                if p_name == "lmstudio"
                else "http://localhost:11434/v1"
            )
            api_key = p_key or "local-key"
            model = p_model or "llama3.2"
            return OpenAIProvider(
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

        if p_name == "openai":
            if p_key:
                return OpenAIProvider(
                    api_key=p_key,
                    model=p_model or "gpt-4o-mini",
                    base_url=p_base_url,
                )
            return MockAIProvider()

        return MockAIProvider()

    primary = _create_single_provider(
        name,
        settings.AI_API_KEY,
        settings.AI_MODEL,
        settings.AI_BASE_URL,
    )

    # Check if a secondary / fallback provider is configured
    fallback_name = (settings.AI_FALLBACK_PROVIDER or "").lower().strip()
    if fallback_name and fallback_name != "none" and fallback_name != name:
        secondary = _create_single_provider(
            fallback_name,
            settings.AI_FALLBACK_API_KEY,
            settings.AI_FALLBACK_MODEL,
            settings.AI_FALLBACK_BASE_URL,
        )
        if not isinstance(secondary, MockAIProvider):
            logger.info(
                "Configured AI with Primary: %s (%s) and Fallback: %s (%s)",
                name,
                settings.AI_MODEL,
                fallback_name,
                settings.AI_FALLBACK_MODEL,
            )
            return FallbackAIProvider(primary=primary, secondary=secondary)

    return primary
