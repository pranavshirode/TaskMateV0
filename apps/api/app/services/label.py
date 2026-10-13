from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.task_label import TaskLabelRepository
from app.schemas.task_label import TaskLabelCreate, TaskLabelResponse


class LabelService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.label_repo = TaskLabelRepository(session)

    async def list_labels(self, user_id: str) -> list[TaskLabelResponse]:
        labels = await self.label_repo.list_by_user(user_id)
        return [TaskLabelResponse.model_validate(lbl) for lbl in labels]

    async def create_label(self, user_id: str, data: TaskLabelCreate) -> TaskLabelResponse:
        label = await self.label_repo.get_or_create(user_id, data.name, data.color)
        return TaskLabelResponse.model_validate(label)
