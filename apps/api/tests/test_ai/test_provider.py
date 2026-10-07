"""Tests for AI provider abstraction."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.errors import (
    AIAuthenticationError,
    AINotConfiguredError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
)
from app.ai.providers.base import AIMessage, AIProvider, MessageRole, ModelInfo
from app.ai.providers.factory import create_ai_provider, reset_ai_provider
from app.ai.providers.openai import OpenAIProvider


class TestAIProviderBase:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            AIProvider()


class TestOpenAIProvider:
    def test_requires_api_key(self):
        with pytest.raises(AINotConfiguredError):
            OpenAIProvider(api_key="")

    def test_model_info(self):
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        info = provider.get_model_info()
        assert info.provider == "openai"
        assert info.model == "gpt-4o-mini"
        assert info.supports_json_mode is True

    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = OpenAIProvider(api_key="test-key")

        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"intent": "CREATE_TASK"}'
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response.model = "gpt-4o-mini"

        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [AIMessage(role=MessageRole.USER, content="Create a task")]
        response = await provider.generate(messages)

        assert response.content == '{"intent": "CREATE_TASK"}'
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 20
        assert response.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_generate_auth_error(self):
        import openai
        provider = OpenAIProvider(api_key="bad-key")
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            side_effect=openai.AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401),
                body=None,
            )
        )

        messages = [AIMessage(role=MessageRole.USER, content="test")]
        with pytest.raises(AIAuthenticationError):
            await provider.generate(messages)

    @pytest.mark.asyncio
    async def test_generate_timeout(self):
        import openai
        provider = OpenAIProvider(api_key="test-key", max_retries=1)
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=MagicMock())
        )

        messages = [AIMessage(role=MessageRole.USER, content="test")]
        with pytest.raises(AITimeoutError):
            await provider.generate(messages)

    @pytest.mark.asyncio
    async def test_generate_rate_limit(self):
        import openai
        provider = OpenAIProvider(api_key="test-key", max_retries=1)
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError(
                message="Rate limit",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        messages = [AIMessage(role=MessageRole.USER, content="test")]
        with pytest.raises(AIRateLimitError):
            await provider.generate(messages)


class TestProviderFactory:
    def setup_method(self):
        reset_ai_provider()

    def test_create_openai_provider(self):
        settings = MagicMock()
        settings.AI_PROVIDER = "openai"
        settings.AI_API_KEY = "test-key"
        settings.AI_MODEL = "gpt-4o-mini"
        settings.AI_BASE_URL = None
        settings.AI_TIMEOUT = 30
        settings.AI_MAX_RETRIES = 3
        settings.AI_TEMPERATURE = 0.1
        settings.AI_MAX_TOKENS = 2000

        provider = create_ai_provider(settings)
        assert isinstance(provider, OpenAIProvider)

    def test_unknown_provider_raises(self):
        settings = MagicMock()
        settings.AI_PROVIDER = "unknown"

        with pytest.raises(ValueError, match="Unknown AI provider"):
            create_ai_provider(settings)

    def test_missing_api_key(self):
        settings = MagicMock()
        settings.AI_PROVIDER = "openai"
        settings.AI_API_KEY = ""
        settings.AI_MODEL = "gpt-4o-mini"
        settings.AI_BASE_URL = None
        settings.AI_TIMEOUT = 30
        settings.AI_MAX_RETRIES = 3
        settings.AI_TEMPERATURE = 0.1
        settings.AI_MAX_TOKENS = 2000

        with pytest.raises(AINotConfiguredError):
            create_ai_provider(settings)
