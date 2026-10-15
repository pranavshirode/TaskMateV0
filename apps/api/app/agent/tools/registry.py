"""Tool registry for the agent system.

All tools must be explicitly registered here.
The agent can only use tools from this registry.
"""

import logging

from app.agent.tools.base import AgentTool, ToolPermission
from app.ai.providers.base import ToolDefinition

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available agent tools.

    Tools are explicitly registered — the agent cannot
    invoke arbitrary functions. This is a security boundary.
    """

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        """Register a tool. Raises ValueError if name already exists."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s (%s)", tool.name, tool.permission.value)

    def unregister_prefix(self, prefix: str) -> None:
        """Remove every tool whose name starts with `prefix`."""
        for name in [n for n in self._tools if n.startswith(prefix)]:
            del self._tools[name]

    def get(self, tool_name: str) -> AgentTool | None:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[AgentTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_by_permission(self, *permissions: ToolPermission) -> list[AgentTool]:
        """List tools filtered by permission level."""
        return [tool for tool in self._tools.values() if tool.permission in permissions]

    def get_tool_definitions(self, tool_names: list[str] | None = None) -> list[ToolDefinition]:
        """Get ToolDefinition objects for the AI provider.

        Args:
            tool_names: Optional filter. If None, returns all tools.

        Returns:
            List of ToolDefinition for the AI provider's generate() call.
        """
        tools = self._tools.values()
        if tool_names:
            tools = [t for t in tools if t.name in tool_names]

        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.input_schema,
            )
            for tool in tools
        ]

    def is_registered(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self._tools

    @property
    def tool_count(self) -> int:
        """Number of registered tools."""
        return len(self._tools)


def create_default_registry() -> ToolRegistry:
    """Create a ToolRegistry with all TaskMate tools registered.

    This is called during application startup. GitHub tools
    are always registered but permission-checked at runtime.
    """
    registry = ToolRegistry()

    from app.agent.tools.client_tools import get_client_tools
    from app.agent.tools.github_tools import get_github_tools
    from app.agent.tools.milestone_tools import get_milestone_tools
    from app.agent.tools.project_tools import get_project_tools
    from app.agent.tools.proposal_tools import get_proposal_tools
    from app.agent.tools.task_tools import get_task_tools

    for tool in get_task_tools():
        registry.register(tool)
    for tool in get_project_tools():
        registry.register(tool)
    for tool in get_client_tools():
        registry.register(tool)
    for tool in get_github_tools():
        registry.register(tool)

    return registry


def create_extended_registry() -> ToolRegistry:
    """Create a ToolRegistry including milestones, proposals, and requirements tools."""
    registry = create_default_registry()
    from app.agent.tools.communication_tools import get_communication_tools
    from app.agent.tools.milestone_tools import get_milestone_tools
    from app.agent.tools.proposal_tools import get_proposal_tools

    for tool in get_milestone_tools():
        registry.register(tool)
    for tool in get_proposal_tools():
        registry.register(tool)
    for tool in get_communication_tools():
        registry.register(tool)
    return registry
