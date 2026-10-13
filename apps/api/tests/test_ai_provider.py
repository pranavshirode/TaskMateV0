import pytest

from app.ai.errors import AIProviderError
from app.ai.providers import get_ai_provider
from app.ai.providers.base import AIMessage
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_mock_provider_generation():
    provider = MockAIProvider()
    assert await provider.health_check() is True

    messages = [
        AIMessage(role="system", content="You are TaskMate AI"),
        AIMessage(role="user", content="Create a task to build login page"),
    ]
    resp = await provider.generate(messages)
    assert resp.content is not None
    assert "CREATE_TASK" in resp.content
    assert resp.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_canned_response():
    provider = MockAIProvider(canned_response='{"intent": "CUSTOM", "confidence": 1.0}')
    resp = await provider.generate([AIMessage(role="user", content="hello")])
    assert "CUSTOM" in resp.content


@pytest.mark.asyncio
async def test_openai_provider_without_key_raises_error():
    provider = OpenAIProvider(api_key="")
    assert await provider.health_check() is False
    with pytest.raises(AIProviderError, match="OpenAI API key not configured"):
        await provider.generate([AIMessage(role="user", content="hi")])


def test_get_ai_provider_factory():
    provider = get_ai_provider(provider_type="mock")
    assert isinstance(provider, MockAIProvider)
