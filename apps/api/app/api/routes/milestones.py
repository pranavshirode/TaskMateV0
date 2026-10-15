"""Milestone and task dependency API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    TaskDependencyCreate,
    TaskDependencyResponse,
)
from app.services.milestone import MilestoneService

router = APIRouter()


def _get_milestone_service(db: AsyncSession = Depends(get_db)) -> MilestoneService:
    return MilestoneService(db)


def _to_response(m) -> MilestoneResponse:
    tasks = getattr(m, "tasks", []) or []
    completed_statuses = {"COMPLETED", "TaskStatus.COMPLETED"}
    return MilestoneResponse(
        id=m.id,
        project_id=m.project_id,
        user_id=m.user_id,
        title=m.title,
        description=m.description,
        status=m.status,
        due_date=m.due_date,
        task_count=len(tasks),
        completed_task_count=sum(
            1 for t in tasks if str(getattr(t, "status", "")) in completed_statuses
        ),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _dep_to_response(d) -> TaskDependencyResponse:
    dep_task = getattr(d, "depends_on", None)
    return TaskDependencyResponse(
        id=d.id,
        task_id=d.task_id,
        depends_on_task_id=d.depends_on_task_id,
        depends_on_title=dep_task.title if dep_task else None,
        depends_on_status=str(dep_task.status) if dep_task else None,
        created_at=d.created_at,
    )


# ── Milestones ─────────────────────────────────────────────────────────────────

@router.post("/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Create a new project milestone."""
    m = await service.create_milestone(str(current_user.id), data)
    return _to_response(m)


@router.get("/milestones/project/{project_id}", response_model=list[MilestoneResponse])
async def list_milestones(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """List all milestones for a project."""
    items = await service.list_milestones(str(current_user.id), project_id)
    return [_to_response(m) for m in items]


@router.get("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Get a single milestone with task counts."""
    m = await service.get_milestone(str(current_user.id), milestone_id)
    return _to_response(m)


@router.patch("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: str,
    data: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Update a milestone's title, status, description, or due date."""
    m = await service.update_milestone(str(current_user.id), milestone_id, data)
    return _to_response(m)


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Delete a milestone (tasks are unlinked, not deleted)."""
    await service.delete_milestone(str(current_user.id), milestone_id)


# ── Task Dependencies ─────────────────────────────────────────────────────────

@router.post("/tasks/{task_id}/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
async def add_task_dependency(
    task_id: str,
    data: TaskDependencyCreate,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Add a dependency: task_id blocks on depends_on_task_id completing first."""
    dep = await service.add_task_dependency(str(current_user.id), task_id, data.depends_on_task_id)
    return _dep_to_response(dep)


@router.get("/tasks/{task_id}/dependencies", response_model=list[TaskDependencyResponse])
async def get_task_dependencies(
    task_id: str,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Get all dependencies for a task."""
    deps = await service.get_task_dependencies(str(current_user.id), task_id)
    return [_dep_to_response(d) for d in deps]


@router.delete(
    "/tasks/{task_id}/dependencies/{depends_on_task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_task_dependency(
    task_id: str,
    depends_on_task_id: str,
    current_user: User = Depends(get_current_user),
    service: MilestoneService = Depends(_get_milestone_service),
):
    """Remove a task dependency edge."""
    await service.remove_task_dependency(str(current_user.id), task_id, depends_on_task_id)

