"""Repository for Project Context Notes and Explicit Memory."""
from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirements import ProjectContextNote
from app.repositories.base import BaseRepository


class ProjectContextNoteRepository(BaseRepository[ProjectContextNote]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProjectContextNote, session)

    async def list_by_project(
        self,
        project_id: str,
        user_id: str,
        include_superseded: bool = False,
    ) -> list[ProjectContextNote]:
        stmt = select(ProjectContextNote).where(
            and_(
                ProjectContextNote.project_id == project_id,
                ProjectContextNote.user_id == user_id,
            )
        )
        if not include_superseded:
            stmt = stmt.where(ProjectContextNote.is_superseded.is_(False))
        stmt = stmt.order_by(ProjectContextNote.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_notes_for_context(
        self,
        project_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[ProjectContextNote]:
        stmt = (
            select(ProjectContextNote)
            .where(
                and_(
                    ProjectContextNote.project_id == project_id,
                    ProjectContextNote.user_id == user_id,
                    ProjectContextNote.is_superseded.is_(False),
                )
            )
            .order_by(ProjectContextNote.is_confirmed.desc(), ProjectContextNote.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

