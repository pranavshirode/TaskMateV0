"""OpenAI provider implementation.

Supports GPT-4o, GPT-4o-mini, and other OpenAI-compatible models.
Includes timeout, retry with exponential backoff, and error mapping.
"""

import logging
import time
from typing import Any, Optional

import openai
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError, AuthenticationError

import json

from app.ai.errors import (
    AIAuthenticationError,
    AIProviderError,
    AIRateLimitError,
    AIResponseError,
    AITimeoutError,
    AINotConfiguredError,
)
from app.ai.providers.base import (
    AIMessage,
    AIProvider,
    AIResponse,
    MessageRole,
    ModelInfo,
    TokenUsage,
    ToolCallRequest,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API provider.

    Wraps the OpenAI async client with retry logic,
    error mapping, and token usage extraction.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        default_temperature: float = 0.1,
        default_max_tokens: int = 2000,
    ):
        if not api_key:
            raise AINotConfiguredError()

        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=float(timeout),
            max_retries=0,  # We handle retries ourselves
        )

    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: Optional[dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        tool_choice: Optional[str] = None,
    ) -> AIResponse:
        """Generate a completion using the OpenAI API."""
        openai_messages = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    m["name"] = msg.name
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
                if not msg.content:
                    m["content"] = None
            openai_messages.append(m)

        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "messages": openai_messages,
            "temperature": temperature if temperature is not None else self._default_temperature,
            "max_tokens": max_tokens or self._default_max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                start_time = time.monotonic()
                response = await self._client.chat.completions.create(**kwargs)
                latency_ms = int((time.monotonic() - start_time) * 1000)

                content = response.choices[0].message.content or ""
                usage = TokenUsage(
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                )

                logger.info(
                    "OpenAI request completed",
                    extra={
                        "model": kwargs["model"],
                        "latency_ms": latency_ms,
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "attempt": attempt,
                    },
                )

                tool_calls = []
                if response.choices[0].message.tool_calls:
                    for tc in response.choices[0].message.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except (json.JSONDecodeError, TypeError):
                            args = {}
                        tool_calls.append(ToolCallRequest(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=args,
                        ))

                return AIResponse(
                    content=content,
                    usage=usage,
                    model=response.model,
                    finish_reason=response.choices[0].finish_reason or "",
                    tool_calls=tool_calls,
                )

            except AuthenticationError as e:
                logger.error("OpenAI authentication failed")
                raise AIAuthenticationError() from e

            except RateLimitError as e:
                logger.warning("OpenAI rate limit hit, attempt %d/%d", attempt, self._max_retries)
                last_error = e
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise AIRateLimitError() from e

            except APITimeoutError as e:
                logger.warning("OpenAI timeout, attempt %d/%d", attempt, self._max_retries)
                last_error = e
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise AITimeoutError() from e

            except APIConnectionError as e:
                logger.warning("OpenAI connection error, attempt %d/%d", attempt, self._max_retries)
                last_error = e
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise AIProviderError() from e

            except APIError as e:
                logger.error("OpenAI API error: status=%s", e.status_code)
                last_error = e
                if e.status_code and e.status_code >= 500 and attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise AIProviderError() from e

            except Exception as e:
                logger.error("Unexpected error during OpenAI request", exc_info=True)
                raise AIProviderError() from e

        # Should not reach here, but just in case
        raise AIProviderError() from last_error

    def get_model_info(self) -> ModelInfo:
        """Return OpenAI model information."""
        return ModelInfo(
            provider="openai",
            model=self._model,
            max_tokens=self._default_max_tokens,
            supports_json_mode=True,
            supports_tool_calling=True,
            supports_streaming=True,
        )

    async def health_check(self) -> bool:
        """Check if the OpenAI API is reachable."""
        try:
            await self._client.models.list()
            return True
        except Exception:
            logger.warning("OpenAI health check failed", exc_info=True)
            return False

    @staticmethod
    async def _backoff(attempt: int) -> None:
        """Exponential backoff with jitter."""
        import asyncio
        import random
        delay = min(2 ** attempt + random.uniform(0, 1), 10)
        await asyncio.sleep(delay)
