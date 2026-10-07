import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.schemas.client import Client, ClientCreate, ClientUpdate, ClientListResponse
from app.services.client import ClientService
from app.api.dependencies import get_current_user, get_client_service

router = APIRouter()

@router.get("/", response_model=ClientListResponse)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> Any:
    items, total = await client_service.list_clients(current_user, skip=skip, limit=limit, search=search)
    return {"items": items, "page": skip // limit + 1, "page_size": limit, "total": total}

@router.post("/", response_model=Client)
async def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> Any:
    return await client_service.create_client(current_user, client_in)

@router.get("/{client_id}", response_model=Client)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> Any:
    client = await client_service.get_client(client_id, current_user)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.patch("/{client_id}", response_model=Client)
async def update_client(
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> Any:
    client = await client_service.update_client(client_id, current_user, client_in)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.delete("/{client_id}", response_model=Client)
async def archive_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> Any:
    client = await client_service.archive_client(client_id, current_user)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
