import uuid
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.schemas.task import (
    Task, TaskCreate, TaskUpdate, TaskStatusUpdate,
    TaskPriorityUpdate, TaskListResponse, TaskEvent
)
from app.services.task import TaskService
from app.api.dependencies import get_current_user, get_task_service

router = APIRouter()

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    items, total = await task_service.list_tasks(
        current_user, skip=skip, limit=limit,
        project_id=project_id, client_id=client_id,
        status=status, priority=priority, search=search
    )
    return {"items": items, "page": skip // limit + 1, "page_size": limit, "total": total}

@router.post("/", response_model=Task)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    try:
        return await task_service.create_task(current_user, task_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    task = await task_service.get_task(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    try:
        task = await task_service.update_task(task_id, current_user, task_in)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}", response_model=Task)
async def archive_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    task = await task_service.archive_task(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: uuid.UUID,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    task = await task_service.change_status(task_id, current_user, status_update.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}/priority", response_model=Task)
async def update_task_priority(
    task_id: uuid.UUID,
    priority_update: TaskPriorityUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    task = await task_service.change_priority(task_id, current_user, priority_update.priority)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/{task_id}/events", response_model=List[TaskEvent])
async def get_task_events(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Any:
    try:
        return await task_service.get_task_events(task_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
