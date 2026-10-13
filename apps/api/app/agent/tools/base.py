"""Base tool interface for the agent system.

Every tool must implement AgentTool. Tools are explicitly
registered — no automatic discovery of arbitrary functions.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.models.user import User


class ToolPermission(str, Enum):
    """Permission level required to execute a tool."""

    READ = "READ"
    WRITE = "WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"


@dataclass
class ToolContext:
    """Context passed to every tool execution.

    Contains the authenticated user and execution metadata.
    Never contains raw credentials or API keys.
    """

    user: User
    execution_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    extra: dict[str, Any] = field(default_factory=dict)  # For service injection


@dataclass
class ToolResult:
    """Normalized result from a tool execution.

    Every tool returns this format so the agent
    can understand results consistently.
    """

    success: bool
    data: dict[str, Any] | None = None
    error: dict[str, str] | None = None  # {"type": "...", "message": "..."}

    @classmethod
    def ok(cls, data: dict[str, Any]) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_type: str, message: str) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error={"type": error_type, "message": message})


class AgentTool(ABC):
    """Abstract base class for all agent tools.

    Every tool must define:
    - name: Dot-separated tool name (e.g., 'task.create')
    - description: What the tool does (sent to LLM)
    - input_schema: JSON Schema for input validation
    - permission: READ, WRITE, or DESTRUCTIVE

    Tools are explicitly registered in the ToolRegistry.
    The agent cannot invoke unregistered tools.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name using dot notation (e.g., 'task.create')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description (sent to LLM)."""
        ...

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for validating tool input."""
        ...

    @property
    @abstractmethod
    def permission(self) -> ToolPermission:
        """Permission level required."""
        ...

    @abstractmethod
    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the tool with validated input.

        Args:
            input_data: Validated input matching input_schema.
            context: Execution context with user and metadata.

        Returns:
            Normalized ToolResult.
        """
        ...

    def to_llm_definition(self) -> dict[str, Any]:
        """Convert to the format expected by the AI provider."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }
