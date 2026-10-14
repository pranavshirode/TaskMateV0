"""Service layer for GitHub integration."""

import httpx

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.integrations.github.client import GitHubClient
from app.models.github_integration import GitHubIntegration
from app.models.user import User
from app.repositories.github_integration import GitHubIntegrationRepository


class GitHubIntegrationService:
    """Business logic for GitHub integration."""

    # Tests replace this with an httpx.MockTransport; production uses real HTTP.
    transport: httpx.AsyncBaseTransport | None = None

    def __init__(self, repository: GitHubIntegrationRepository):
        self.repository = repository

    async def get_integration(self, user: User) -> GitHubIntegration | None:
        """Get the user's GitHub integration status without secrets."""
        return await self.repository.get_by_user_id(user.id)

    async def connect(self, user: User, access_token: str, scopes: str | None = None) -> GitHubIntegration:
        """Connect or update a GitHub integration using an access token."""
        settings = get_settings()
        # 1. Instantiate client to test token and get user info
        client = GitHubClient(access_token)
        github_user = await client.get_authenticated_user()

        # 2. Encrypt token
        if not settings.token_encryption_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY is not configured")
        encrypted_token = encrypt_token(access_token, settings.token_encryption_key)

        # 3. Save
        return await self.repository.create_or_update(
            user_id=user.id,
            github_user_id=github_user.id,
            username=github_user.login,
            encrypted_access_token=encrypted_token,
            scopes=scopes,
            avatar_url=github_user.avatar_url,
        )

    async def exchange_oauth_code(self, code: str) -> str:
        """Exchange a GitHub OAuth `code` (from the redirect) for an access token, server-side."""
        settings = get_settings()
        if not (settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET):
            raise ValueError("GitHub OAuth is not configured; paste a personal access token instead")
        async with httpx.AsyncClient(timeout=15, transport=self.transport) as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
            )
        payload = resp.json() if resp.content else {}
        if resp.status_code != 200 or "access_token" not in payload:
            raise ValueError(payload.get("error_description") or "GitHub rejected the authorization code")
        return str(payload["access_token"])

    async def disconnect(self, user: User) -> bool:
        """Disconnect the user's GitHub integration."""
        return await self.repository.delete_by_user_id(user.id)

    async def get_decrypted_token(self, user: User) -> str | None:
        """Get the decrypted access token for the user."""
        settings = get_settings()
        integration = await self.repository.get_by_user_id(user.id)
        if not integration:
            return None

        if not settings.token_encryption_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY is not configured")

        return decrypt_token(integration.encrypted_access_token, settings.token_encryption_key)

    async def create_client(self, user: User) -> GitHubClient:
        """Create a GitHub API client for the user.

        Raises:
            ValueError: If the user hasn't connected GitHub or if decryption fails.
        """
        token = await self.get_decrypted_token(user)
        if not token:
            raise ValueError("GitHub account is not connected")

        return GitHubClient(token)
