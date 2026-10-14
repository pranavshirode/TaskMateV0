"""Minimal, defensive MCP client used by the agent.

Each call opens a short-lived streamable-HTTP session (the servers TaskMate uses are stateless),
with a hard timeout, so a slow or broken MCP server can never hang an agent run.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import httpx
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


class MCPError(Exception):
    """An MCP failure with a message that is safe to show to the user."""


def _leaf_errors(exc: BaseException) -> list[BaseException]:
    nested = getattr(exc, "exceptions", None)
    if nested:
        return [leaf for e in nested for leaf in _leaf_errors(e)]
    return [exc]


def describe_error(exc: BaseException) -> str:
    """Turn transport/protocol failures (often wrapped in ExceptionGroups) into a short explanation."""
    for leaf in _leaf_errors(exc):
        if isinstance(leaf, httpx.HTTPStatusError):
            code = leaf.response.status_code
            if code in (401, 403):
                return "the server rejected the account's credentials (reconnect it in Settings → Integrations)"
            return f"the server returned HTTP {code}"
        if isinstance(leaf, (httpx.ConnectError, ConnectionError)):
            return "the server is unreachable"
        if isinstance(leaf, (TimeoutError, httpx.TimeoutException)):
            return "the server timed out"
        if isinstance(leaf, MCPError):
            return str(leaf)
    return "an unexpected MCP error occurred"


class MCPClientManager:
    def __init__(self, timeout: float = 20, cache_seconds: float = 300):
        self.timeout = timeout
        self.cache_seconds = cache_seconds
        self._tool_cache: dict[str, tuple[float, list[types.Tool]]] = {}

    @asynccontextmanager
    async def _session(self, url: str, headers: dict[str, str]) -> AsyncIterator[ClientSession]:
        async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as http:
            async with streamable_http_client(url, http_client=http) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    @staticmethod
    def cache_key(url: str, headers: dict[str, str]) -> str:
        # Keyed by credentials too, so a reconnected (different) account never sees a stale tool list.
        raw = url + "\n" + "\n".join(f"{k}:{v}" for k, v in sorted(headers.items()))
        return hashlib.sha256(raw.encode()).hexdigest()

    async def list_tools(self, url: str, headers: dict[str, str]) -> list[types.Tool]:
        key = self.cache_key(url, headers)
        cached = self._tool_cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_seconds:
            return cached[1]
        try:
            with anyio.fail_after(self.timeout):
                async with self._session(url, headers) as session:
                    tools = (await session.list_tools()).tools
        except Exception as e:
            raise MCPError(describe_error(e)) from e
        self._tool_cache[key] = (time.monotonic(), tools)
        return tools

    async def call_tool(
        self, url: str, headers: dict[str, str], name: str, arguments: dict[str, Any]
    ) -> types.CallToolResult:
        try:
            with anyio.fail_after(self.timeout):
                async with self._session(url, headers) as session:
                    return await session.call_tool(name, arguments)
        except Exception as e:
            raise MCPError(describe_error(e)) from e

    def clear_cache(self) -> None:
        self._tool_cache.clear()


_manager: MCPClientManager | None = None


def get_mcp_manager() -> MCPClientManager:
    global _manager
    if _manager is None:
        from app.core.config import get_settings

        settings = get_settings()
        _manager = MCPClientManager(timeout=settings.MCP_TIMEOUT, cache_seconds=settings.MCP_TOOL_CACHE_SECONDS)
    return _manager
