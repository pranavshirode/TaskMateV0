"""Integrations API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Optional
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_github_integration_service
from app.models.user import User
from app.services.github_integration import GitHubIntegrationService
from app.core.config import get_settings


router = APIRouter()


class GitHubStatusResponse(BaseModel):
    connected: bool
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class GitHubConnectRequest(BaseModel):
    access_token: str
    scopes: Optional[str] = None


@router.get("/github", response_model=GitHubStatusResponse)
async def get_github_status(
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> Any:
    """Get the current user's GitHub integration status."""
    integration = await github_service.get_integration(current_user)
    if integration:
        return {
            "connected": True,
            "username": integration.username,
            "avatar_url": integration.avatar_url,
        }
    return {"connected": False}


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
        await github_service.connect(current_user, request.access_token, request.scopes)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect GitHub: {e}")


@router.delete("/github")
async def disconnect_github(
    current_user: User = Depends(get_current_user),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> Any:
    """Disconnect the current user's GitHub integration."""
    await github_service.disconnect(current_user)
    return {"status": "success"}

