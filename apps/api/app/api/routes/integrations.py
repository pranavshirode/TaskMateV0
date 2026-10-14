"""Integrations API routes."""

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_github_integration_service, get_google_integration_service
from app.core.config import get_settings
from app.core.errors import ValidationError
from app.integrations.mcp import get_mcp_manager, load_mcp_tools
from app.models.user import User
from app.services.github_integration import GitHubIntegrationService
from app.services.google_integration import GoogleIntegrationError, GoogleIntegrationService

router = APIRouter()


class GitHubStatusResponse(BaseModel):
    connected: bool
    username: str | None = None
    avatar_url: str | None = None
    oauth_available: bool = False  # "Sign in with GitHub" configured on the server (else: paste a token)


class GitHubConnectRequest(BaseModel):
    """Either a personal access token, or the `code` from GitHub's OAuth redirect."""

    access_token: str | None = None
    code: str | None = None
    scopes: str | None = None


@router.get("/github", response_model=GitHubStatusResponse)
async def get_github_status(
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> Any:
    """Get the current user's GitHub integration status."""
    integration = await github_service.get_integration(current_user)
    settings = get_settings()
    oauth_available = bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
    if integration:
        return {
            "connected": True,
            "username": integration.username,
            "avatar_url": integration.avatar_url,
            "oauth_available": oauth_available,
        }
    return {"connected": False, "oauth_available": oauth_available}


@router.get("/github/authorize")
async def get_github_authorize_url() -> Any:
    """Get the GitHub OAuth authorize URL."""
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub integration is not configured")

    url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=repo,user:email"
    )
    return {"url": url}


@router.post("/github/connect")
async def connect_github(
    request: GitHubConnectRequest,
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> Any:
    """Connect a GitHub account using an access token."""
    try:
        token = request.access_token or (
            await github_service.exchange_oauth_code(request.code) if request.code else None
        )
        if not token:
            raise ValueError("Provide a personal access token or an OAuth code")
        integration = await github_service.connect(current_user, token.strip(), request.scopes)
        get_mcp_manager().clear_cache()
        return {"status": "success", "connected": True, "username": integration.username}
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            message = "GitHub rejected this token. Check it was copied completely and hasn't expired."
        else:
            message = f"GitHub returned HTTP {e.response.status_code}. Try again in a moment."
        raise HTTPException(status_code=400, detail=message) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail="Could not reach GitHub. Check your internet connection.") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect GitHub: {e}") from e


@router.delete("/github")
async def disconnect_github(
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> Any:
    """Disconnect the current user's GitHub integration."""
    await github_service.disconnect(current_user)
    get_mcp_manager().clear_cache()
    return {"status": "success"}


# ---------------------------------------------------------------- Google (per-user OAuth)


class GoogleStatusResponse(BaseModel):
    configured: bool  # server has Google OAuth credentials
    connected: bool
    email: str | None = None


class GoogleConnectRequest(BaseModel):
    code: str
    state: str


@router.get("/google", response_model=GoogleStatusResponse)
async def get_google_status(
    current_user: User = Depends(get_current_user),
    google_service: GoogleIntegrationService = Depends(get_google_integration_service),
) -> Any:
    integration = await google_service.get_integration(current_user)
    return {
        "configured": google_service.is_configured(),
        "connected": integration is not None,
        "email": integration.google_email if integration else None,
    }


@router.get("/google/authorize")
async def get_google_authorize_url(
    current_user: User = Depends(get_current_user),
    google_service: GoogleIntegrationService = Depends(get_google_integration_service),
) -> Any:
    """URL for the browser to start Google sign-in (state is bound to the current user)."""
    try:
        return {"url": google_service.authorization_url(current_user)}
    except GoogleIntegrationError as e:
        raise ValidationError(str(e), code="GOOGLE_NOT_CONFIGURED") from e


@router.post("/google/connect", response_model=GoogleStatusResponse)
async def connect_google(
    request: GoogleConnectRequest,
    current_user: User = Depends(get_current_user),
    google_service: GoogleIntegrationService = Depends(get_google_integration_service),
) -> Any:
    """Finish Google sign-in: called by the frontend callback page with Google's `code` and `state`."""
    try:
        integration = await google_service.connect(current_user, request.code, request.state)
    except GoogleIntegrationError as e:
        raise ValidationError(str(e), code="GOOGLE_CONNECT_FAILED") from e
    get_mcp_manager().clear_cache()
    return {"configured": True, "connected": True, "email": integration.google_email}


@router.delete("/google")
async def disconnect_google(
    current_user: User = Depends(get_current_user),
    google_service: GoogleIntegrationService = Depends(get_google_integration_service),
) -> Any:
    await google_service.disconnect(current_user)
    get_mcp_manager().clear_cache()
    return {"status": "success"}


# ---------------------------------------------------------------- MCP status


class MCPToolInfo(BaseModel):
    name: str
    permission: str


class MCPServerStatusResponse(BaseModel):
    key: str
    label: str
    configured: bool
    connected: bool
    account: str | None = None
    error: str | None = None
    tool_count: int = 0
    tools: list[MCPToolInfo] = []


@router.get("/mcp", response_model=list[MCPServerStatusResponse])
async def get_mcp_status(
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
    google_service: GoogleIntegrationService = Depends(get_google_integration_service),
) -> Any:
    """Which MCP servers the current user's agent can use right now, and with which tools."""
    _, statuses = await load_mcp_tools(
        current_user, {"github_service": github_service, "google_service": google_service}
    )
    return [vars(s) for s in statuses]
