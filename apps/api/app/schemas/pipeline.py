"""Pydantic schemas for the end-to-end Multi-Agent Pipeline workflow."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class PipelineStageLog(BaseModel):
    stage_name: str
    status: str  # PENDING, RUNNING, COMPLETED, PAUSED_FOR_CLARIFICATION, AWAITING_APPROVAL, SKIPPED, FAILED
    duration_ms: int = 0
    summary: str
    error: Optional[str] = None


class PipelineExecuteRequest(BaseModel):
    project_id: str
    brief: str = Field(min_length=5)
    title: Optional[str] = None
    desired_outcome: Optional[str] = None
    constraints: Optional[str] = None
    deadline: Optional[str] = None
    auto_approve_requirements: bool = False
    auto_create_tasks: bool = False
    auto_create_proposal: bool = True


class PipelineResumeRequest(BaseModel):
    analysis_id: str
    auto_approve_requirements: bool = False
    auto_create_tasks: bool = False
    auto_create_proposal: bool = True


class PipelineExecutionResponse(BaseModel):
    execution_id: str
    project_id: str
    analysis_id: str
    status: str  # SUCCESS, PARTIAL_SUCCESS, CLARIFICATION_REQUIRED, PENDING_REQUIREMENT_APPROVAL, FAILED
    stages: list[PipelineStageLog]
    requirements_count: int = 0
    unresolved_questions_count: int = 0
    planned_tasks_count: int = 0
    created_tasks_count: int = 0
    proposal_id: Optional[str] = None
    message: str
    total_duration_ms: int = 0

