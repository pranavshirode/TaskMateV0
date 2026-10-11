"""Base AI provider interface.

All AI providers must implement this interface. The application code
uses only this abstraction — never provider-specific APIs directly.
"""
from __future__ import annotations

import abc
import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class MessageRole(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolDefinition:
    """Definition of a tool the LLM can call."""
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCallRequest:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AIMessage:
    """A message in the conversation sent to the AI provider."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class AIResponse:
    """Standardised response from any AI provider."""
    content: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    finish_reason: str = ""
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@dataclass
class ModelInfo:
    provider: str
    model: str
    max_tokens: int
    supports_json_mode: bool = False
    supports_tool_calling: bool = False
    supports_streaming: bool = False


class BaseAIProvider(abc.ABC):
    """Abstract base class for AI providers.

    Supports:
    - Text generation
    - Structured JSON output
    - Tool calling, streaming, local models
    """

    @abc.abstractmethod
    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        tools: Optional[list[ToolDefinition]] = None,
        tool_choice: Optional[str] = None,
    ) -> AIResponse:
        """Generate a completion from the AI model."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and configured."""
        ...


AIProvider = BaseAIProvider
