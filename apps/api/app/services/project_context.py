"""Project Context Notes and Memory Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.enums import ContextCategory
from app.models.requirements import ProjectContextNote
from app.repositories.project import ProjectRepository
from app.repositories.project_context import ProjectContextNoteRepository
from app.schemas.requirements import ProjectContextNoteCreate, ProjectContextNoteUpdate


class ProjectContextService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectContextNoteRepository(db)
        self.project_repo = ProjectRepository(db)

    async def _verify_project_ownership(self, user_id: str, project_id: str) -> None:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by authenticated user")

    async def create_note(self, user_id: str, project_id: str, data: ProjectContextNoteCreate) -> ProjectContextNote:
        await self._verify_project_ownership(user_id, project_id)

        try:
            category_enum = ContextCategory(data.category.upper())
        except ValueError:
            category_enum = ContextCategory.DECISION

        note = ProjectContextNote(
            project_id=project_id,
            user_id=user_id,
            title=data.title.strip(),
            content=data.content.strip(),
            category=category_enum,
            source=data.source,
            is_confirmed=data.is_confirmed,
            is_superseded=False,
        )
        return await self.repo.create(note)

    async def list_notes(
        self, user_id: str, project_id: str, include_superseded: bool = False
    ) -> list[ProjectContextNote]:
        await self._verify_project_ownership(user_id, project_id)
        return await self.repo.list_by_project(project_id, user_id, include_superseded)

    async def get_note(self, user_id: str, note_id: str) -> ProjectContextNote:
        note = await self.repo.get_by_id_and_user(note_id, user_id)
        if not note:
            raise NotFoundError("Project context note not found")
        return note

    async def update_note(self, user_id: str, note_id: str, data: ProjectContextNoteUpdate) -> ProjectContextNote:
        note = await self.get_note(user_id, note_id)

        if data.title is not None:
            note.title = data.title.strip()
        if data.content is not None:
            note.content = data.content.strip()
        if data.category is not None:
            try:
                note.category = ContextCategory(data.category.upper())
            except ValueError as err:
                raise ValidationError(f"Invalid category: {data.category}") from err
        if data.is_confirmed is not None:
            note.is_confirmed = data.is_confirmed
        if data.is_superseded is not None:
            note.is_superseded = data.is_superseded

        note.updated_at = datetime.now(timezone.utc)
        return await self.repo.update(note)

    async def mark_superseded(
        self, user_id: str, note_id: str, superseded_by_id: str | None = None
    ) -> ProjectContextNote:
        note = await self.get_note(user_id, note_id)
        note.is_superseded = True
        note.superseded_by_id = superseded_by_id
        note.updated_at = datetime.now(timezone.utc)
        return await self.repo.update(note)

    async def delete_note(self, user_id: str, note_id: str) -> None:
        note = await self.get_note(user_id, note_id)
        await self.repo.delete(note)
