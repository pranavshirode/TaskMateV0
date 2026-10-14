"""API endpoints for Workflow Automations and Daily Summaries."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_workflow_automation_service
from app.models.user import User
from app.schemas.requirements import (
    AutomationExecutionResponse,
    DailyProjectSummaryResponse,
)
from app.services.workflow_automation import WorkflowAutomationService

router = APIRouter()


@router.post("/projects/{project_id}/daily-summary", response_model=DailyProjectSummaryResponse)
async def generate_project_daily_summary(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowAutomationService = Depends(get_workflow_automation_service),
):
    return await service.generate_daily_project_summary(str(current_user.id), project_id)


@router.post("/projects/{project_id}/sync-consistency")
async def sync_project_task_consistency(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowAutomationService = Depends(get_workflow_automation_service),
) -> dict[str, Any]:
    return await service.sync_task_consistency(str(current_user.id), project_id)


@router.get("/executions", response_model=list[AutomationExecutionResponse])
async def list_automation_executions(
    project_id: str | None = None,
    current_user: User = Depends(get_current_user),
    service: WorkflowAutomationService = Depends(get_workflow_automation_service),
):
    return await service.list_executions(str(current_user.id), project_id=project_id)
