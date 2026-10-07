import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.schemas.repository import Repository, RepositoryCreate, RepositoryUpdate
from app.services.repository import RepositoryService
from app.api.dependencies import get_current_user, get_repository_service

router = APIRouter()

@router.get("/projects/{project_id}/repositories", response_model=List[Repository])
async def list_repositories(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> Any:
    try:
        return await repository_service.list_repositories(project_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/projects/{project_id}/repositories", response_model=Repository)
async def create_repository(
    project_id: uuid.UUID,
    repository_in: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> Any:
    if str(repository_in.project_id) != str(project_id):
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    try:
        return await repository_service.create_repository(current_user, repository_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repositories/{repository_id}", response_model=Repository)
async def get_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> Any:
    repository = await repository_service.get_repository(repository_id, current_user)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository

@router.patch("/repositories/{repository_id}", response_model=Repository)
async def update_repository(
    repository_id: uuid.UUID,
    repository_in: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> Any:
    repository = await repository_service.update_repository(repository_id, current_user, repository_in)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository

@router.delete("/repositories/{repository_id}", response_model=dict)
async def delete_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> Any:
    success = await repository_service.delete_repository(repository_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"message": "Repository deleted"}
