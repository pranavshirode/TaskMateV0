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
)
from app.ai.errors import (
    AIProviderError,
)
from app.ai.errors import (
    AIRateLimitError as AppAIRateLimitError,
)
from app.ai.errors import (
    AITimeoutError as AppAITimeoutError,
)
from app.ai.providers.base import (
    AIMessage,
    AIResponse,
    BaseAIProvider,
    ModelInfo,
    ToolCallRequest,
    ToolDefinition,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI / OpenAI-compatible API provider (supports Gemini, OpenAI, Ollama, LM Studio, vLLM)."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.AI_API_KEY
        self._default_model = model or settings.AI_MODEL
        self._base_url = base_url or settings.AI_BASE_URL
        self._default_temperature = settings.AI_TEMPERATURE
        self._default_max_tokens = settings.AI_MAX_TOKENS
        self._timeout = settings.AI_TIMEOUT
        self._max_retries = settings.AI_MAX_RETRIES

        self._client = (
            AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url or None,
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
        tools: list[ToolDefinition] | None = None,
        tool_choice: Any = None,
    ) -> AIResponse:
        if not self._client:
            raise AIProviderError("OpenAI API key not configured")

        chosen_model = model or self._default_model
        chosen_temperature = temperature if temperature is not None else self._default_temperature
        chosen_max_tokens = max_tokens or self._default_max_tokens

        openai_messages = [_to_openai_message(m) for m in messages]

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
                    if "JSON" not in (msg["content"] or ""):
                        msg["content"] += "\n\nYou MUST respond with valid JSON only."
                    break

        # OpenAI function names may not contain dots, so "task.create" is sent as "task__create".
        tool_names: dict[str, str] = {}
        if tools:
            tool_names = {_encode_tool_name(t.name): t.name for t in tools}
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": _encode_tool_name(t.name),
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        start_time = time.time()
        try:
            response = await self._client.chat.completions.create(**kwargs)
        except APITimeoutError as e:
            raise AppAITimeoutError(f"OpenAI request timed out after {self._timeout}s") from e
        except RateLimitError as e:
            raise AppAIRateLimitError("OpenAI rate limit exceeded") from e
        except AuthenticationError as e:
            raise AppAIAuthenticationError("OpenAI authentication failed — check AI_API_KEY") from e
        except APIError as e:
            raise AIProviderError(f"OpenAI API error: {e.message}") from e
        except Exception as e:
            raise AIProviderError(f"Unexpected OpenAI error: {str(e)}") from e

        latency_ms = int((time.time() - start_time) * 1000)
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage

        tool_calls = []
        for tc in choice.message.tool_calls or []:
            try:
                arguments = json.loads(tc.function.arguments or "{}")
            except (json.JSONDecodeError, TypeError):
                arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            name = tool_names.get(tc.function.name, tc.function.name)
            extra_content = getattr(tc, "extra_content", None)
            if extra_content is None and hasattr(tc, "model_extra") and tc.model_extra:
                extra_content = tc.model_extra.get("extra_content")
            tool_calls.append(ToolCallRequest(id=tc.id, name=name, arguments=arguments, extra_content=extra_content))

        return AIResponse(
            content=content,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency_ms,
            finish_reason=choice.finish_reason or "",
            tool_calls=tool_calls,
            raw={"finish_reason": choice.finish_reason},
        )

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="openai",
            model=self._default_model,
            max_tokens=self._default_max_tokens,
            supports_json_mode=True,
            supports_tool_calling=True,
        )

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False


def _encode_tool_name(name: str) -> str:
    return name.replace(".", "__")


def _to_openai_message(message: AIMessage) -> dict[str, Any]:
    role = getattr(message.role, "value", message.role)
    payload: dict[str, Any] = {"role": role, "content": message.content}
    if role == "assistant" and message.tool_calls:
        payload["content"] = message.content or None
        tool_calls_payload = []
        for tc in message.tool_calls:
            tc_dict: dict[str, Any] = {
                "id": tc.id,
                "type": "function",
                "function": {"name": _encode_tool_name(tc.name), "arguments": json.dumps(tc.arguments)},
            }
            if getattr(tc, "extra_content", None):
                tc_dict["extra_content"] = tc.extra_content
            tool_calls_payload.append(tc_dict)
        payload["tool_calls"] = tool_calls_payload
    if role == "tool":
        payload["tool_call_id"] = message.tool_call_id
    return payload
