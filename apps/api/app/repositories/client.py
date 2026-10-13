from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.enums import ClientStatus
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: AsyncSession):
        super().__init__(Client, session)

    async def create(self, data: dict) -> Client:
        client = Client(**data)
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def update(self, client: Client, data: dict) -> Client:
        for key, value in data.items():
            setattr(client, key, value)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def list_by_user(
        self,
        user_id: str,
        search: str | None = None,
        status: ClientStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Client], int]:
        query = select(self.model).where(self.model.user_id == user_id)

        if search:
            query = query.where(
                or_(
                    self.model.name.ilike(f"%{search}%"),
                    self.model.company_name.ilike(f"%{search}%"),
                )
            )

        if status:
            query = query.where(self.model.status == status)

        # Sorting — whitelist allowed fields
        sort_column = getattr(self.model, sort_by, self.model.created_at)
        if sort_by not in ["created_at", "updated_at", "name"]:
            sort_column = self.model.created_at

        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return await self.paginate(query, page, page_size)
