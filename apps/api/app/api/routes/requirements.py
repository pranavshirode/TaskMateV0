"""API endpoints for Requirements Analysis and Traceability."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_requirements_service
from app.models.user import User
from app.schemas.requirements import (
    AnswerClarificationRequest,
    ApproveTaskPlanRequest,
    ApproveTaskPlanResponse,
    ClarificationQuestionSchema,
    GenerateTaskPlanResponse,
    RequirementSchema,
    RequirementsAnalysisCreate,
    RequirementsAnalysisDetail,
    RequirementsAnalysisSummary,
    RequirementUpdate,
    TraceabilityResponse,
)
from app.services.requirements_pipeline import RequirementsService

router = APIRouter()


@router.post("/", response_model=RequirementsAnalysisDetail, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: RequirementsAnalysisCreate,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analysis = await service.create_analysis(str(current_user.id), data)
    return analysis


@router.get("/project/{project_id}", response_model=list[RequirementsAnalysisSummary])
async def list_project_analyses(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analyses = await service.list_by_project(str(current_user.id), project_id)
    summaries = []
    for a in analyses:
        total_reqs = len(a.requirements)
        approved_reqs = sum(1 for r in a.requirements if r.status.value == "APPROVED" or str(r.status) == "APPROVED")
        unresolved_q = sum(1 for q in a.questions if q.status.value == "UNRESOLVED" or str(q.status) == "UNRESOLVED")
        summaries.append(
            RequirementsAnalysisSummary(
                id=a.id,
                project_id=a.project_id,
                user_id=a.user_id,
                title=a.title,
                brief=a.brief,
                status=a.status.value if hasattr(a.status, "value") else str(a.status),
                version=a.version,
                approved_at=a.approved_at,
                created_at=a.created_at,
                updated_at=a.updated_at,
                total_requirements=total_reqs,
                approved_requirements=approved_reqs,
                unresolved_questions=unresolved_q,
            )
        )
    return summaries


@router.get("/{analysis_id}", response_model=RequirementsAnalysisDetail)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analysis = await service.get_analysis(str(current_user.id), analysis_id)
    return analysis


@router.post("/{analysis_id}/analyze", response_model=RequirementsAnalysisDetail)
async def analyze_brief(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analysis = await service.analyze(str(current_user.id), analysis_id)
    return analysis


@router.post("/{analysis_id}/questions/{question_id}/answer", response_model=ClarificationQuestionSchema)
async def answer_clarification(
    analysis_id: str,
    question_id: str,
    data: AnswerClarificationRequest,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    question = await service.answer_question(str(current_user.id), analysis_id, question_id, data.answer)
    return question


@router.put("/{analysis_id}/requirements/{requirement_id}", response_model=RequirementSchema)
async def update_requirement(
    analysis_id: str,
    requirement_id: str,
    data: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    req = await service.update_requirement(str(current_user.id), analysis_id, requirement_id, data)
    return req


@router.post("/{analysis_id}/approve", response_model=RequirementsAnalysisDetail)
async def approve_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analysis = await service.approve_analysis(str(current_user.id), analysis_id)
    return analysis


@router.post("/{analysis_id}/archive", response_model=RequirementsAnalysisDetail)
async def archive_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    analysis = await service.archive_analysis(str(current_user.id), analysis_id)
    return analysis


@router.post("/{analysis_id}/generate-task-plan", response_model=GenerateTaskPlanResponse)
async def generate_task_plan(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    return await service.generate_task_plan(str(current_user.id), analysis_id)


@router.post("/{analysis_id}/approve-task-plan", response_model=ApproveTaskPlanResponse)
async def approve_task_plan(
    analysis_id: str,
    data: ApproveTaskPlanRequest,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    return await service.approve_task_plan(str(current_user.id), analysis_id, data)


@router.get("/{analysis_id}/traceability", response_model=TraceabilityResponse)
async def get_traceability(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    service: RequirementsService = Depends(get_requirements_service),
):
    return await service.get_traceability(str(current_user.id), analysis_id)

