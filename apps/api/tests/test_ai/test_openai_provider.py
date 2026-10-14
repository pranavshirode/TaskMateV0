"""OpenAIProvider request/response mapping, tested against a fake client (no network)."""

import json
from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, RateLimitError

from app.ai.errors import AIAuthenticationError, AIProviderError, AIRateLimitError, AITimeoutError
from app.ai.providers.base import AIMessage, MessageRole, ToolCallRequest, ToolDefinition
from app.ai.providers.openai_provider import OpenAIProvider


def _completion(content="", tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason="tool_calls" if tool_calls else "stop")],
        model="gpt-test",
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7, total_tokens=18),
    )


class FakeCompletions:
    def __init__(self, result):
        self.result = result
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _provider(result) -> tuple[OpenAIProvider, FakeCompletions]:
    provider = OpenAIProvider(api_key="sk-test")
    completions = FakeCompletions(result)
    provider._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return provider, completions


TOOLS = [ToolDefinition(name="task.create", description="Create a task", parameters={"type": "object"})]


async def test_sends_tools_with_openai_safe_names():
    provider, completions = _provider(_completion("ok"))

    await provider.generate([AIMessage(role=MessageRole.USER, content="hi")], tools=TOOLS)

    sent = completions.kwargs["tools"][0]["function"]
    assert sent["name"] == "task__create"
    assert sent["parameters"] == {"type": "object"}


async def test_parses_tool_calls_and_restores_names():
    call = SimpleNamespace(
        id="call_1", function=SimpleNamespace(name="task__create", arguments=json.dumps({"title": "Ship it"}))
    )
    provider, _ = _provider(_completion(tool_calls=[call]))

    response = await provider.generate([AIMessage(role=MessageRole.USER, content="hi")], tools=TOOLS)

    assert response.tool_calls == [ToolCallRequest(id="call_1", name="task.create", arguments={"title": "Ship it"})]
    assert (response.input_tokens, response.output_tokens) == (11, 7)


async def test_malformed_tool_arguments_become_empty_dict():
    call = SimpleNamespace(id="c", function=SimpleNamespace(name="task__create", arguments="{not json"))
    provider, _ = _provider(_completion(tool_calls=[call]))

    response = await provider.generate([AIMessage(role=MessageRole.USER, content="hi")], tools=TOOLS)

    assert response.tool_calls[0].arguments == {}


async def test_tool_round_trip_messages_are_well_formed():
    provider, completions = _provider(_completion("done"))
    history = [
        AIMessage(role=MessageRole.USER, content="make a task"),
        AIMessage(
            role=MessageRole.ASSISTANT,
            content="",
            tool_calls=[ToolCallRequest(id="c1", name="task.create", arguments={"title": "x"})],
        ),
        AIMessage(role=MessageRole.TOOL, content='{"id": "1"}', tool_call_id="c1", name="task.create"),
    ]

    await provider.generate(history, tools=TOOLS)

    assistant, tool = completions.kwargs["messages"][1:]
    assert assistant["tool_calls"][0]["function"] == {"name": "task__create", "arguments": '{"title": "x"}'}
    assert assistant["content"] is None
    assert tool == {"role": "tool", "content": '{"id": "1"}', "tool_call_id": "c1"}


_REQUEST = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (APITimeoutError(request=_REQUEST), AITimeoutError),
        (RateLimitError("slow down", response=httpx.Response(429, request=_REQUEST), body=None), AIRateLimitError),
        (
            AuthenticationError("bad key", response=httpx.Response(401, request=_REQUEST), body=None),
            AIAuthenticationError,
        ),
        (RuntimeError("boom"), AIProviderError),
    ],
)
async def test_maps_sdk_errors(error, expected):
    provider, _ = _provider(error)

    with pytest.raises(expected):
        await provider.generate([AIMessage(role=MessageRole.USER, content="hi")])
