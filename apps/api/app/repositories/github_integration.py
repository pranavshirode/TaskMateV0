"""Repository for GitHub integration persistence."""

import uuid
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import GitHubIntegration


class GitHubIntegrationRepository:
    """Data access for GitHub integrations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[GitHubIntegration]:
        """Get integration for a user."""
        stmt = select(GitHubIntegration).where(GitHubIntegration.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: uuid.UUID,
        github_user_id: Optional[int],
        username: Optional[str],
        encrypted_access_token: str,
        scopes: Optional[str],
        avatar_url: Optional[str],
    ) -> GitHubIntegration:
        """Create or update integration for a user."""
        integration = await self.get_by_user_id(user_id)
        
        if integration:
            integration.github_user_id = github_user_id
            integration.username = username
            integration.encrypted_access_token = encrypted_access_token
            integration.scopes = scopes
            integration.avatar_url = avatar_url
        else:
            integration = GitHubIntegration(
                user_id=user_id,
                github_user_id=github_user_id,
                username=username,
                encrypted_access_token=encrypted_access_token,
                scopes=scopes,
                avatar_url=avatar_url,
            )
            self.session.add(integration)
            
        await self.session.commit()
        await self.session.refresh(integration)
        return integration

    async def delete_by_user_id(self, user_id: uuid.UUID) -> bool:
        """Delete integration for a user."""
        stmt = delete(GitHubIntegration).where(GitHubIntegration.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

