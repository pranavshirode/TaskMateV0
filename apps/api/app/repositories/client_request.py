"""Repositories for Client Requests and Automation Executions."""
from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirements import ClientRequest, AutomationExecution
from app.repositories.base import BaseRepository


class ClientRequestRepository(BaseRepository[ClientRequest]):
    def __init__(self, session: AsyncSession):
        super().__init__(ClientRequest, session)

    async def list_by_project(self, project_id: str, user_id: str) -> list[ClientRequest]:
        stmt = (
            select(ClientRequest)
            .where(
                and_(
                    ClientRequest.project_id == project_id,
                    ClientRequest.user_id == user_id,
                )
            )
            .order_by(ClientRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AutomationExecutionRepository(BaseRepository[AutomationExecution]):
    def __init__(self, session: AsyncSession):
        super().__init__(AutomationExecution, session)

    async def list_by_user(self, user_id: str, limit: int = 50) -> list[AutomationExecution]:
        stmt = (
            select(AutomationExecution)
            .where(AutomationExecution.user_id == user_id)
            .order_by(AutomationExecution.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_project(self, project_id: str, user_id: str) -> list[AutomationExecution]:
        stmt = (
            select(AutomationExecution)
            .where(
                and_(
                    AutomationExecution.project_id == project_id,
                    AutomationExecution.user_id == user_id,
                )
            )
            .order_by(AutomationExecution.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

