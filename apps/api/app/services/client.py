import uuid
from typing import Optional, Tuple, List
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate, Client
from app.models.user import User

class ClientService:
    def __init__(self, repository: ClientRepository):
        self.repository = repository

    async def get_client(self, client_id: uuid.UUID, user: User) -> Optional[Client]:
        return await self.repository.get(client_id=client_id, user_id=user.id)

    async def list_clients(self, user: User, skip: int = 0, limit: int = 20, search: Optional[str] = None) -> Tuple[List[Client], int]:
        items = await self.repository.list(user_id=user.id, skip=skip, limit=limit, search=search)
        total = await self.repository.count(user_id=user.id, search=search)
        return items, total

    async def create_client(self, user: User, obj_in: ClientCreate) -> Client:
        return await self.repository.create(user_id=user.id, obj_in=obj_in)

    async def update_client(self, client_id: uuid.UUID, user: User, obj_in: ClientUpdate) -> Optional[Client]:
        db_obj = await self.get_client(client_id, user)
        if not db_obj:
            return None
        return await self.repository.update(db_obj=db_obj, obj_in=obj_in)

    async def archive_client(self, client_id: uuid.UUID, user: User) -> Optional[Client]:
        db_obj = await self.get_client(client_id, user)
        if not db_obj:
            return None
        return await self.repository.archive(db_obj=db_obj)
