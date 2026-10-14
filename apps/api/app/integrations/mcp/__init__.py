"""MCP (Model Context Protocol) integration: lets the agent use external tools (GitHub, Google Workspace)."""

from __future__ import annotations

import logging
from typing import Any

from app.agent.tools.base import AgentTool
from app.core.config import get_settings
from app.integrations.mcp.client import MCPClientManager, MCPError, get_mcp_manager
from app.integrations.mcp.servers import MCPServerStatus, resolve_servers
from app.integrations.mcp.tools import MCPTool, name_fits
from app.models.user import User

logger = logging.getLogger(__name__)

__all__ = ["MCPTool", "MCPServerStatus", "load_mcp_tools", "get_mcp_manager"]


async def load_mcp_tools(
    user: User, services: dict[str, Any], manager: MCPClientManager | None = None
) -> tuple[list[AgentTool], list[MCPServerStatus]]:
    """Discover the MCP tools available to this user. Never raises: failures are reported per server."""
    manager = manager or get_mcp_manager()
    limit = get_settings().MCP_MAX_TOOLS_PER_SERVER
    tools: list[AgentTool] = []
    statuses: list[MCPServerStatus] = []

    for status, connection in await resolve_servers(user, services):
        statuses.append(status)
        if connection is None:
            continue
        try:
            remote_tools = await manager.list_tools(connection.url, connection.headers)
        except MCPError as e:
            status.error = str(e)
            logger.warning("MCP server %s unavailable for user %s: %s", status.key, user.id, e)
            continue
        usable = [t for t in remote_tools if name_fits(connection.key, t.name)][:limit]
        if len(remote_tools) > len(usable):
            logger.info("MCP server %s: using %d of %d tools", status.key, len(usable), len(remote_tools))
        for remote in usable:
            tool = MCPTool(connection, remote, manager)
            tools.append(tool)
            status.tools.append({"name": tool.name, "permission": tool.permission.value})
        status.tool_count = len(usable)
    return tools, statuses
