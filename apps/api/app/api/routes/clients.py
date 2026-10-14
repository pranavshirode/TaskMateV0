from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import ClientStatus
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import PaginatedResponse
from app.services.client import ClientService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    search: str | None = None,
    status: ClientStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.list(
        user_id=current_user.id,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.create(current_user.id, data)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.get(current_user.id, client_id)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.update(current_user.id, client_id, data)


@router.delete("/{client_id}", response_model=ClientResponse)
async def archive_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.archive(current_user.id, client_id)
