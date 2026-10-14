"""Persistence for per-user Google connections."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.google_integration import GoogleIntegration


class GoogleIntegrationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> GoogleIntegration | None:
        result = await self.session.execute(select(GoogleIntegration).where(GoogleIntegration.user_id == str(user_id)))
        return result.scalar_one_or_none()

    async def save(self, integration: GoogleIntegration) -> GoogleIntegration:
        self.session.add(integration)
        await self.session.commit()
        await self.session.refresh(integration)
        return integration

    async def delete_by_user_id(self, user_id: str) -> bool:
        result = await self.session.execute(delete(GoogleIntegration).where(GoogleIntegration.user_id == str(user_id)))
        await self.session.commit()
        return bool(result.rowcount)  # type: ignore[attr-defined]
