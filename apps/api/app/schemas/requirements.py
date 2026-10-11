"""Pydantic schemas for Requirements Analysis, Memory, Client Requests, and Automation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Requirements Analysis ---

class RequirementsAnalysisCreate(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)
    brief: str = Field(..., min_length=5)
    desired_outcome: Optional[str] = None
    constraints: Optional[str] = None
    deadline: Optional[str] = None
    repository_id: Optional[str] = None


class RequirementsAnalysisUpdate(BaseModel):
    title: Optional[str] = None
    brief: Optional[str] = None
    desired_outcome: Optional[str] = None
    constraints: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    acceptance_criteria: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None


class AnswerClarificationRequest(BaseModel):
    answer: str = Field(..., min_length=1)


class RequirementSchema(BaseModel):
    id: str
    analysis_id: str
    key: str
    category: str
    title: str
    description: str
    priority: str
    status: str
    acceptance_criteria: Optional[list[Any]] = None
    dependencies: Optional[list[Any]] = None
    open_questions: Optional[list[Any]] = None
    created_at: datetime
    updated_at: datetime
    # Traceability metrics
    linked_task_count: int = 0
    completed_task_count: int = 0
    progress_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ClarificationQuestionSchema(BaseModel):
    id: str
    analysis_id: str
    question_key: str
    question: str
    reason: Optional[str] = None
    context_topic: Optional[str] = None
    answer: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementAssumptionSchema(BaseModel):
    id: str
    analysis_id: str
    description: str
    reason: Optional[str] = None
    confidence: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementRiskSchema(BaseModel):
    id: str
    analysis_id: str
    description: str
    risk_type: str
    severity: str
    mitigation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementsAnalysisSummary(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    brief: str
    status: str
    version: int
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    total_requirements: int = 0
    approved_requirements: int = 0
    unresolved_questions: int = 0

    model_config = ConfigDict(from_attributes=True)


class RequirementsAnalysisDetail(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    brief: str
    desired_outcome: Optional[str] = None
    constraints: Optional[str] = None
    deadline: Optional[str] = None
    repository_id: Optional[str] = None
    status: str
    version: int
    overview_data: Optional[dict[str, Any]] = None
    technical_constraints: Optional[list[Any]] = None
    non_functional_requirements: Optional[list[Any]] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    requirements: list[RequirementSchema] = []
    questions: list[ClarificationQuestionSchema] = []
    assumptions: list[RequirementAssumptionSchema] = []
    risks: list[RequirementRiskSchema] = []
    implementation_progress_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# --- Task Planning ---

class TaskPlanItem(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "TODO"
    deadline: Optional[str] = None
    linked_requirement_keys: list[str] = []
    acceptance_criteria: Optional[list[str]] = None
    estimated_effort: Optional[str] = None


class GenerateTaskPlanResponse(BaseModel):
    analysis_id: str
    proposed_tasks: list[TaskPlanItem]
    rationale: str
    generated_at: datetime


class ApproveTaskPlanRequest(BaseModel):
    selected_tasks: list[TaskPlanItem]
    idempotency_key: Optional[str] = None


class CreatedTaskResult(BaseModel):
    id: str
    title: str
    priority: str
    status: str
    linked_requirements: list[str] = []


class ApproveTaskPlanResponse(BaseModel):
    analysis_id: str
    created_tasks_count: int
    tasks: list[CreatedTaskResult]
    traceability_links_created: int
    message: str


# --- Traceability ---

class TaskTraceabilityInfo(BaseModel):
    id: str
    title: str
    status: str
    priority: str


class RequirementTraceabilityItem(BaseModel):
    requirement_id: str
    key: str
    title: str
    status: str
    priority: str
    progress_percent: float
    linked_tasks: list[TaskTraceabilityInfo]


class TraceabilityResponse(BaseModel):
    analysis_id: str
    total_requirements: int
    implemented_requirements: int
    unimplemented_requirements: int
    overall_progress_percent: float
    items: list[RequirementTraceabilityItem]


# --- Project Context Memory ---

class ProjectContextNoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = "DECISION"  # DECISION, CONSTRAINT, CLIENT_PREFERENCE, ARCHITECTURAL_NOTE
    source: str = "MANUAL"
    is_confirmed: bool = True


class ProjectContextNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_confirmed: Optional[bool] = None
    is_superseded: Optional[bool] = None


class ProjectContextNoteResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    content: str
    category: str
    source: str
    is_confirmed: bool
    is_superseded: bool
    superseded_by_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Client Requests ---

class ClientRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    request_type: str = "NEW_FEATURE"  # NEW_FEATURE, CHANGE_REQUEST, BUG_REPORT, CLARIFICATION, OUT_OF_SCOPE


class ClientRequestImpactResponse(BaseModel):
    request_id: str
    request_type: str
    classification_explanation: str
    affected_requirements: list[str] = []
    affected_tasks: list[str] = []
    scope_change_summary: str
    recommended_actions: list[str] = []


class ClientRequestResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    content: str
    request_type: str
    status: str
    impact_summary: Optional[dict[str, Any]] = None
    analysis_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Automations & Summaries ---

class DailyProjectSummaryResponse(BaseModel):
    project_id: str
    project_name: str
    generated_at: datetime
    completed_recently: list[dict[str, Any]]
    in_progress: list[dict[str, Any]]
    due_soon: list[dict[str, Any]]
    overdue: list[dict[str, Any]]
    unresolved_requirements: list[dict[str, Any]]
    pending_clarification_questions: list[dict[str, Any]]
    active_blockers: list[dict[str, Any]]
    summary_text: str


class AutomationExecutionResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str] = None
    automation_type: str
    status: str
    trigger: str
    result_data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
