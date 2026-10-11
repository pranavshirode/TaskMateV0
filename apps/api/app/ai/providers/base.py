"""Base AI provider interface.

All AI providers must implement this interface. The application code
uses only this abstraction — never provider-specific APIs directly.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class AIMessage:
    """A message in the conversation sent to the AI provider."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class AIResponse:
    """Standardised response from any AI provider."""
    content: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    raw: dict = field(default_factory=dict)


class BaseAIProvider(abc.ABC):
    """Abstract base class for AI providers.

    Supports:
    - Text generation
    - Structured JSON output
    - Future: tool calling, streaming, local models
    """

    @abc.abstractmethod
    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> AIResponse:
        """Generate a completion from the AI model.

        Args:
            messages: Conversation messages (system + user + assistant).
            response_format: Optional JSON schema for structured output.
            temperature: Sampling temperature override.
            max_tokens: Max output tokens override.
            model: Model override.

        Returns:
            AIResponse with content and usage metadata.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and configured."""
        ...
