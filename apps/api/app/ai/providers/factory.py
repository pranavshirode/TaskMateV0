"""Compatibility wrapper kept for scripts (e.g. evaluation/evaluate.py).

The application uses ``app.ai.providers.get_ai_provider``; this module delegates to it.
"""

from app.ai.providers import get_ai_provider
from app.ai.providers.base import BaseAIProvider
from app.core.config import Settings


def create_ai_provider(settings: Settings | None = None) -> BaseAIProvider:
    return get_ai_provider(settings.AI_PROVIDER if settings else None)


def reset_ai_provider() -> None:
    """Providers are created per call, so there is no cached instance to reset."""
