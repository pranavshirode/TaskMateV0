"""Abstract AI provider interface.

All AI providers must implement this interface to ensure
the application is provider-independent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MessageRole(str, Enum):
    """Message roles for AI conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolDefinition:
    """Definition of a tool the LLM can call."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@dataclass
class ToolCallRequest:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AIMessage:
    """A single message in an AI conversation."""
    role: MessageRole
    content: str
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    tool_call_id: Optional[str] = None  # For TOOL role messages
    name: Optional[str] = None  # Tool name for TOOL role messages


@dataclass
class TokenUsage:
    """Token usage statistics from an AI request."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class AIResponse:
    """Response from an AI provider."""
    content: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: str = ""
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    raw_response: Any = None  # Provider-specific, never expose to user


@dataclass
class ModelInfo:
    """Information about the current AI model."""
    provider: str
    model: str
    max_tokens: int
    supports_json_mode: bool = False
    supports_tool_calling: bool = False
    supports_streaming: bool = False


class AIProvider(ABC):
    """Abstract base class for all AI providers.

    Implementations must handle:
    - Text generation
    - Structured output (JSON mode)
    - Tool/function calling
    - Timeout and retry logic
    - Error mapping to AIError subclasses
    - Token usage tracking

    Future capabilities (not yet required):
    - Streaming responses
    - Local model inference
    """

    @abstractmethod
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
        """Generate a completion from the AI model.

        Args:
            messages: Conversation messages.
            response_format: Optional JSON schema for structured output.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            model: Override default model.
            tools: Optional list of tool definitions for tool calling.
            tool_choice: Optional tool choice strategy ('auto', 'none', or specific tool name).

        Returns:
            AIResponse with content, usage stats, and optional tool_calls.
        """
        ...

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Return information about the current model configuration."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and configured."""
        ...
