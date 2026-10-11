"""Service layer for GitHub integration."""

import uuid
from typing import Optional

from app.core.config import get_settings
from app.core.encryption import encrypt_token, decrypt_token
from app.models.user import User
from app.models.github_integration import GitHubIntegration
from app.repositories.github_integration import GitHubIntegrationRepository
from app.integrations.github.client import GitHubClient


class GitHubIntegrationService:
    """Business logic for GitHub integration."""

    def __init__(self, repository: GitHubIntegrationRepository):
        self.repository = repository

    async def get_integration(self, user: User) -> Optional[GitHubIntegration]:
        """Get the user's GitHub integration status without secrets."""
        return await self.repository.get_by_user_id(user.id)

    async def connect(self, user: User, access_token: str, scopes: Optional[str] = None) -> GitHubIntegration:
        """Connect or update a GitHub integration using an access token."""
        settings = get_settings()
        # 1. Instantiate client to test token and get user info
        client = GitHubClient(access_token)
        github_user = await client.get_authenticated_user()

        # 2. Encrypt token
        if not settings.GITHUB_ENCRYPTION_KEY:
            raise ValueError("GITHUB_ENCRYPTION_KEY is not configured")
        encrypted_token = encrypt_token(access_token, settings.GITHUB_ENCRYPTION_KEY)

        # 3. Save
        return await self.repository.create_or_update(
            user_id=user.id,
            github_user_id=github_user.id,
            username=github_user.login,
            encrypted_access_token=encrypted_token,
            scopes=scopes,
            avatar_url=github_user.avatar_url,
        )

    async def disconnect(self, user: User) -> bool:
        """Disconnect the user's GitHub integration."""
        return await self.repository.delete_by_user_id(user.id)

    async def get_decrypted_token(self, user: User) -> Optional[str]:
        """Get the decrypted access token for the user."""
        settings = get_settings()
        integration = await self.repository.get_by_user_id(user.id)
        if not integration:
            return None

        if not settings.GITHUB_ENCRYPTION_KEY:
            raise ValueError("GITHUB_ENCRYPTION_KEY is not configured")

        return decrypt_token(integration.encrypted_access_token, settings.GITHUB_ENCRYPTION_KEY)

    async def create_client(self, user: User) -> GitHubClient:
        """Create a GitHub API client for the user.
        
        Raises:
            ValueError: If the user hasn't connected GitHub or if decryption fails.
        """
        token = await self.get_decrypted_token(user)
        if not token:
            raise ValueError("GitHub account is not connected")
        
        return GitHubClient(token)

