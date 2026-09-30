from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.schemas.common import PaginatedResponse
from app.core.errors import NotFoundError
from app.models.enums import ClientStatus

class ClientService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.client_repo = ClientRepository(session)
        
    async def create(self, user_id: str, data: ClientCreate) -> ClientResponse:
        client_data = data.model_dump()
        client_data["user_id"] = user_id
        client = await self.client_repo.create(client_data)
        return ClientResponse.model_validate(client)
        
    async def get(self, user_id: str, client_id: str) -> ClientResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client or str(client.user_id) != user_id:
            raise NotFoundError("Client not found")
        return ClientResponse.model_validate(client)
        
    async def update(self, user_id: str, client_id: str, data: ClientUpdate) -> ClientResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client or str(client.user_id) != user_id:
            raise NotFoundError("Client not found")
            
        update_data = data.model_dump(exclude_unset=True)
        if "status" in update_data:
            if update_data["status"] == ClientStatus.ARCHIVED and client.status != ClientStatus.ARCHIVED:
                update_data["archived_at"] = datetime.now(timezone.utc)
            elif update_data["status"] != ClientStatus.ARCHIVED and client.status == ClientStatus.ARCHIVED:
                update_data["archived_at"] = None
                
        client = await self.client_repo.update(client, update_data)
        return ClientResponse.model_validate(client)
        
    async def archive(self, user_id: str, client_id: str) -> ClientResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client or str(client.user_id) != user_id:
            raise NotFoundError("Client not found")
            
        if client.status != ClientStatus.ARCHIVED:
            client = await self.client_repo.update(client, {
                "status": ClientStatus.ARCHIVED,
                "archived_at": datetime.now(timezone.utc)
            })
        return ClientResponse.model_validate(client)
        
    async def list(self, user_id: str, search: str | None = None, status: ClientStatus | None = None, 
                   page: int = 1, page_size: int = 20, 
                   sort_by: str = "created_at", sort_order: str = "desc") -> PaginatedResponse[ClientResponse]:
        clients, total = await self.client_repo.list_by_user(
            user_id=user_id, search=search, status=status, 
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items = [ClientResponse.model_validate(c) for c in clients]
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
        
    async def search(self, user_id: str, query: str) -> list[ClientResponse]:
        clients, _ = await self.client_repo.list_by_user(
            user_id=user_id, search=query, page=1, page_size=20
        )
        return [ClientResponse.model_validate(c) for c in clients]

