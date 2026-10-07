import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectListResponse
from app.services.project import ProjectService
from app.api.dependencies import get_current_user, get_project_service

router = APIRouter()

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    client_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Any:
    items, total = await project_service.list_projects(
        current_user, skip=skip, limit=limit, client_id=client_id, status=status, search=search
    )
    return {"items": items, "page": skip // limit + 1, "page_size": limit, "total": total}

@router.post("/", response_model=Project)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Any:
    try:
        return await project_service.create_project(current_user, project_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Any:
    project = await project_service.get_project(project_id, current_user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Any:
    try:
        project = await project_service.update_project(project_id, current_user, project_in)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{project_id}", response_model=Project)
async def archive_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Any:
    project = await project_service.archive_project(project_id, current_user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
