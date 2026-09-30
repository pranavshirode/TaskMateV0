from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import ProjectStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
)
from app.services.project import ProjectService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    search: str | None = None,
    status: ProjectStatus | None = None,
    client_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.list(
        user_id=current_user.id,
        search=search,
        status=status,
        client_id=client_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.create(current_user.id, data)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.get(current_user.id, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.update(current_user.id, project_id, data)


@router.delete("/{project_id}", response_model=ProjectResponse)
async def archive_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.archive(current_user.id, project_id)
