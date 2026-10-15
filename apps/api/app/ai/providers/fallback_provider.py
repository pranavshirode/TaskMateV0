"""Fallback AI provider chaining a primary provider (e.g. Gemini) with a secondary provider (e.g. Ollama)."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.providers.base import (
    AIMessage,
    AIResponse,
    BaseAIProvider,
    ModelInfo,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class FallbackAIProvider(BaseAIProvider):
    """Executes requests using the primary provider, automatically falling back to secondary on failure."""

    def __init__(self, primary: BaseAIProvider, secondary: BaseAIProvider):
        self.primary = primary
        self.secondary = secondary

    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        tools: list[ToolDefinition] | None = None,
        tool_choice: str | None = None,
    ) -> AIResponse:
        try:
            return await self.primary.generate(
                messages,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                tools=tools,
                tool_choice=tool_choice,
            )
        except Exception as e:
            logger.warning(
                "Primary AI provider failed with %s: %s. Falling back to secondary provider...",
                type(e).__name__,
                e,
            )
            return await self.secondary.generate(
                messages,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                model=None,  # let secondary use its configured default model
                tools=tools,
                tool_choice=tool_choice,
            )

    async def health_check(self) -> bool:
        if await self.primary.health_check():
            return True
        return await self.secondary.health_check()

    def get_model_info(self) -> ModelInfo:
        primary_info = self.primary.get_model_info()
        return ModelInfo(
            provider=f"{primary_info.provider}+fallback",
            model=primary_info.model,
            max_tokens=primary_info.max_tokens,
            supports_json_mode=primary_info.supports_json_mode,
            supports_tool_calling=primary_info.supports_tool_calling,
            supports_streaming=primary_info.supports_streaming,
        )
