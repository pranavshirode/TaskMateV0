"""The MCP servers TaskMate's agent can use, resolved per user.

A server is only offered to a user who has connected the matching account; the request carries that
user's own credentials, so tools always act as the signed-in TaskMate user and nobody else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings
from app.models.user import User


@dataclass
class MCPServerConnection:
    key: str  # used in tool names: mcp.<key>.<tool>
    label: str
    url: str
    headers: dict[str, str]
    # Arguments TaskMate fills in itself and hides from the model (e.g. which Google account to use).
    injected_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerStatus:
    key: str
    label: str
    configured: bool
    connected: bool
    account: str | None = None
    error: str | None = None
    tool_count: int = 0
    tools: list[dict[str, str]] = field(default_factory=list)


async def resolve_servers(
    user: User, services: dict[str, Any]
) -> list[tuple[MCPServerStatus, MCPServerConnection | None]]:
    """For each known MCP server: its status for this user, plus connection details if usable."""
    settings = get_settings()
    results: list[tuple[MCPServerStatus, MCPServerConnection | None]] = []

    # GitHub's hosted MCP server, authenticated with the user's own stored GitHub token.
    github = MCPServerStatus(key="github", label="GitHub", configured=bool(settings.MCP_GITHUB_URL), connected=False)
    github_conn = None
    github_service = services.get("github_service")
    if github.configured and github_service is not None:
        try:
            integration = await github_service.get_integration(user)
            if integration is not None:
                token = await github_service.get_decrypted_token(user)
                github.connected, github.account = True, integration.username
                headers = {"Authorization": f"Bearer {token}"}
                if settings.MCP_GITHUB_TOOLSETS:
                    headers["X-MCP-Toolsets"] = settings.MCP_GITHUB_TOOLSETS
                github_conn = MCPServerConnection("github", "GitHub", settings.MCP_GITHUB_URL, headers)
        except Exception as e:
            github.error = str(e)
    results.append((github, github_conn))

    # Google Workspace MCP server (local workspace-mcp), authenticated with the user's Google access token.
    google_service = services.get("google_service")
    google = MCPServerStatus(
        key="google",
        label="Google Workspace",
        configured=bool(settings.MCP_GOOGLE_URL and google_service is not None and google_service.is_configured()),
        connected=False,
    )
    google_conn = None
    if google.configured and google_service is not None:
        try:
            creds = await google_service.get_credentials(user)
            if creds is not None:
                token, email = creds
                google.connected, google.account = True, email
                google_conn = MCPServerConnection(
                    "google",
                    "Google Workspace",
                    settings.MCP_GOOGLE_URL,
                    {"Authorization": f"Bearer {token}"},
                    injected_args={"user_google_email": email},
                )
        except Exception as e:
            google.connected, google.error = True, str(e)
    results.append((google, google_conn))
    return results
