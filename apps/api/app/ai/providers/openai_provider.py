"""OpenAI provider implementation."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import (
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.ai.errors import (
    AIAuthenticationError as AppAIAuthenticationError,
    AIProviderError,
    AIRateLimitError as AppAIRateLimitError,
    AIResponseError,
    AITimeoutError as AppAITimeoutError,
)
from app.ai.providers.base import AIMessage, AIResponse, BaseAIProvider
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI / OpenAI-compatible API provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.AI_API_KEY
        self._default_model = model or settings.AI_MODEL
        self._default_temperature = settings.AI_TEMPERATURE
        self._default_max_tokens = settings.AI_MAX_TOKENS
        self._timeout = settings.AI_TIMEOUT
        self._max_retries = settings.AI_MAX_RETRIES

        self._client = (
            AsyncOpenAI(
                api_key=self._api_key,
                timeout=float(self._timeout),
                max_retries=self._max_retries,
            )
            if self._api_key
            else None
        )

    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> AIResponse:
        if not self._client:
            raise AIProviderError("OpenAI API key not configured")

        chosen_model = model or self._default_model
        chosen_temperature = (
            temperature if temperature is not None else self._default_temperature
        )
        chosen_max_tokens = max_tokens or self._default_max_tokens

        openai_messages: list[dict[str, str]] = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": openai_messages,
            "temperature": chosen_temperature,
            "max_tokens": chosen_max_tokens,
        }

        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
            for msg in openai_messages:
                if msg["role"] == "system":
                    if "JSON" not in msg["content"]:
                        msg["content"] += "\n\nYou MUST respond with valid JSON only."
                    break

        start_time = time.time()
        try:
            response = await self._client.chat.completions.create(**kwargs)
        except APITimeoutError as e:
            raise AppAITimeoutError(f"OpenAI request timed out after {self._timeout}s") from e
        except RateLimitError as e:
            raise AppAIRateLimitError("OpenAI rate limit exceeded") from e
        except AuthenticationError as e:
            raise AppAIAuthenticationError(
                "OpenAI authentication failed — check AI_API_KEY"
            ) from e
        except APIError as e:
            raise AIProviderError(f"OpenAI API error: {e.message}") from e
        except Exception as e:
            raise AIProviderError(f"Unexpected OpenAI error: {str(e)}") from e

        latency_ms = int((time.time() - start_time) * 1000)
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage

        return AIResponse(
            content=content,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency_ms,
            raw={"finish_reason": choice.finish_reason},
        )

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False

