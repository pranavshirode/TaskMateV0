from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_label import TaskLabel
from app.repositories.base import BaseRepository


class TaskLabelRepository(BaseRepository[TaskLabel]):
    def __init__(self, session: AsyncSession):
        super().__init__(TaskLabel, session)

    async def get_or_create(
        self, user_id: str, name: str, color: str | None = None
    ) -> TaskLabel:
        query = select(self.model).where(
            self.model.user_id == user_id, self.model.name == name
        )
        result = await self.session.execute(query)
        label = result.scalar_one_or_none()

        if not label:
            label = self.model(
                user_id=user_id, name=name, color=color or "#808080"
            )
            self.session.add(label)
            await self.session.commit()
            await self.session.refresh(label)

        return label

    async def list_by_user(self, user_id: str) -> list[TaskLabel]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_names(
        self, user_id: str, names: list[str]
    ) -> list[TaskLabel]:
        query = select(self.model).where(
            self.model.user_id == user_id, self.model.name.in_(names)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
