"""Expose a remote MCP tool as a normal TaskMate agent tool."""

from __future__ import annotations

import copy
import json
import logging
from typing import Any

from mcp import types

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult
from app.integrations.mcp.client import MCPClientManager, MCPError
from app.integrations.mcp.servers import MCPServerConnection

logger = logging.getLogger(__name__)

MAX_RESULT_CHARS = 8000  # keep one tool result from flooding the model's context
MAX_NAME_LENGTH = 64  # OpenAI function-name limit (after "." -> "__" encoding)


def mcp_tool_name(server_key: str, remote_name: str) -> str:
    return f"mcp.{server_key}.{remote_name}"


def name_fits(server_key: str, remote_name: str) -> bool:
    return len(mcp_tool_name(server_key, remote_name).replace(".", "__")) <= MAX_NAME_LENGTH


class MCPTool(AgentTool):
    def __init__(self, server: MCPServerConnection, remote: types.Tool, manager: MCPClientManager):
        self.server = server
        self.remote = remote
        self.manager = manager

    @property
    def name(self) -> str:
        return mcp_tool_name(self.server.key, self.remote.name)

    @property
    def description(self) -> str:
        text = (self.remote.description or self.remote.title or self.remote.name).strip()
        return f"[{self.server.label}, external] {text[:900]}"

    @property
    def input_schema(self) -> dict[str, Any]:
        schema = copy.deepcopy(self.remote.inputSchema or {"type": "object", "properties": {}})
        schema.setdefault("type", "object")
        hidden = set(self.server.injected_args)
        schema["properties"] = {k: v for k, v in (schema.get("properties") or {}).items() if k not in hidden}
        if "required" in schema:
            schema["required"] = [r for r in schema["required"] if r not in hidden]
        return schema

    @property
    def permission(self) -> ToolPermission:
        # Trust the server's own annotation only for "read-only"; everything else needs approval.
        annotations = self.remote.annotations
        if annotations is not None and annotations.readOnlyHint is True:
            return ToolPermission.READ
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        # Injected values always win, so the model cannot redirect a call to another account.
        arguments = {**input_data, **self.server.injected_args}
        try:
            result = await self.manager.call_tool(self.server.url, self.server.headers, self.remote.name, arguments)
        except MCPError as e:
            return ToolResult.fail("MCP_ERROR", f"{self.server.label}: {e}")

        text = _result_text(result)
        if result.isError:
            return ToolResult.fail("MCP_TOOL_ERROR", f"{self.server.label}: {text[:500] or 'tool reported an error'}")
        truncated = len(text) > MAX_RESULT_CHARS
        return ToolResult.ok(
            {
                "source": f"{self.server.label} (external, untrusted)",
                "content": text[:MAX_RESULT_CHARS],
                "truncated": truncated,
            }
        )


def _result_text(result: types.CallToolResult) -> str:
    parts = []
    for item in result.content:
        if isinstance(item, types.TextContent):
            parts.append(item.text)
        elif isinstance(item, types.EmbeddedResource) and isinstance(item.resource, types.TextResourceContents):
            parts.append(item.resource.text)
        else:
            parts.append(f"[{item.type} content omitted]")
    if not parts and result.structuredContent:
        parts.append(json.dumps(result.structuredContent, default=str))
    return "\n".join(parts)
