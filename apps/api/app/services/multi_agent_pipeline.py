"""Multi-Agent Orchestration Pipeline Service.

Coordinates specialized AI agents into a bounded, observable sequential workflow:
Client brief → Requirement Analyzer → Clarification Gate → Task Planner → Proposal Generator → Developer Review.

Strictly enforces:
1. Non-fabrication: pauses for clarification when ambiguity or missing facts exist.
2. Approval gating: requirements must be reviewed/approved before downstream action.
3. Duplicate write prevention: idempotent re-runs for tasks and proposals.
4. Comprehensive execution tracing via AutomationExecution logs.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.base import BaseAIProvider
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.enums import AnalysisStatus, AutomationType
from app.models.proposal import Proposal
from app.models.requirements import AutomationExecution, RequirementsAnalysis
from app.repositories.project import ProjectRepository
from app.schemas.pipeline import (
    PipelineExecuteRequest,
    PipelineExecutionResponse,
    PipelineResumeRequest,
    PipelineStageLog,
)
from app.schemas.proposal import AIGenerateProposalRequest
from app.schemas.requirements import ApproveTaskPlanRequest, RequirementsAnalysisCreate
from app.services.proposal import ProposalService
from app.services.requirements_pipeline import RequirementsService
from app.services.task import TaskService

logger = logging.getLogger(__name__)


class MultiAgentPipelineService:
    """Orchestrator for the end-to-end multi-agent delivery workflow."""

    def __init__(
        self,
        db: AsyncSession,
        ai_provider: BaseAIProvider,
        requirements_service: RequirementsService,
        proposal_service: ProposalService,
        task_service: TaskService,
    ) -> None:
        self.db = db
        self.ai_provider = ai_provider
        self.requirements_service = requirements_service
        self.proposal_service = proposal_service
        self.task_service = task_service
        self.project_repo = ProjectRepository(db)

    async def execute_new_brief(
        self, user_id: str, request: PipelineExecuteRequest
    ) -> PipelineExecutionResponse:
        """Initialize and execute the multi-agent pipeline from a new client brief."""
        project = await self.project_repo.get_by_id(request.project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by you")

        # 1. Create identifiable session
        title = request.title or f"Requirements: {project.name}"
        create_dto = RequirementsAnalysisCreate(
            project_id=request.project_id,
            title=title,
            brief=request.brief,
            desired_outcome=request.desired_outcome,
            constraints=request.constraints,
            deadline=request.deadline,
        )
        analysis = await self.requirements_service.create_analysis(user_id, create_dto)

        return await self._run_pipeline(
            user_id=user_id,
            analysis=analysis,
            auto_approve_requirements=request.auto_approve_requirements,
            auto_create_tasks=request.auto_create_tasks,
            auto_create_proposal=request.auto_create_proposal,
        )

    async def resume_pipeline(
        self, user_id: str, request: PipelineResumeRequest
    ) -> PipelineExecutionResponse:
        """Resume execution of an existing pipeline after clarifications or approvals."""
        analysis = await self.requirements_service.get_analysis(user_id, request.analysis_id)
        return await self._run_pipeline(
            user_id=user_id,
            analysis=analysis,
            auto_approve_requirements=request.auto_approve_requirements,
            auto_create_tasks=request.auto_create_tasks,
            auto_create_proposal=request.auto_create_proposal,
        )

    async def _run_pipeline(
        self,
        user_id: str,
        analysis: RequirementsAnalysis,
        auto_approve_requirements: bool,
        auto_create_tasks: bool,
        auto_create_proposal: bool,
    ) -> PipelineExecutionResponse:
        pipeline_started = time.monotonic()
        execution_id = str(uuid.uuid4())
        stages: list[PipelineStageLog] = []

        # Record start in automation audit log
        automation_log = AutomationExecution(
            id=execution_id,
            user_id=user_id,
            project_id=analysis.project_id,
            automation_type=AutomationType.MULTI_AGENT_WORKFLOW,
            status="RUNNING",
            trigger="MULTI_AGENT_PIPELINE",
            result_data={"analysis_id": analysis.id, "stage": "INITIALIZED"},
        )
        self.db.add(automation_log)
        await self.db.commit()

        # ── STAGE 1: Requirement Analyzer Agent ─────────────────────────────────
        t0 = time.monotonic()
        try:
            analysis = await self.requirements_service.analyze(user_id, analysis.id)
            d1 = int((time.monotonic() - t0) * 1000)

            unresolved_q = sum(
                1 for q in analysis.questions if getattr(q.status, "value", str(q.status)) == "UNRESOLVED"
            )
            req_count = len(analysis.requirements)

            if unresolved_q > 0:
                stages.append(
                    PipelineStageLog(
                        stage_name="Requirement Analyzer",
                        status="PAUSED_FOR_CLARIFICATION",
                        duration_ms=d1,
                        summary=f"Extracted {req_count} requirements, but identified {unresolved_q} critical questions needing clarification.",
                    )
                )
                stages.append(
                    PipelineStageLog(
                        stage_name="Task Planner",
                        status="SKIPPED",
                        duration_ms=0,
                        summary="Skipped: Pipeline paused until clarifications are answered.",
                    )
                )
                stages.append(
                    PipelineStageLog(
                        stage_name="Proposal Generator",
                        status="SKIPPED",
                        duration_ms=0,
                        summary="Skipped: Pipeline paused until clarifications are answered.",
                    )
                )

                automation_log.status = "PAUSED"
                automation_log.result_data = {
                    "status": "CLARIFICATION_REQUIRED",
                    "analysis_id": analysis.id,
                    "unresolved_questions": unresolved_q,
                }
                await self.db.commit()

                total_ms = int((time.monotonic() - pipeline_started) * 1000)
                return PipelineExecutionResponse(
                    execution_id=execution_id,
                    project_id=analysis.project_id,
                    analysis_id=analysis.id,
                    status="CLARIFICATION_REQUIRED",
                    stages=stages,
                    requirements_count=req_count,
                    unresolved_questions_count=unresolved_q,
                    message="Requirements analyzed. Pipeline paused: please answer clarification questions before proceeding to task planning.",
                    total_duration_ms=total_ms,
                )

            stages.append(
                PipelineStageLog(
                    stage_name="Requirement Analyzer",
                    status="COMPLETED",
                    duration_ms=d1,
                    summary=f"Analyzed brief into {req_count} structured requirements with zero pending ambiguities.",
                )
            )

        except Exception as e:
            logger.exception("Requirement Analyzer failed")
            d1 = int((time.monotonic() - t0) * 1000)
            stages.append(
                PipelineStageLog(
                    stage_name="Requirement Analyzer",
                    status="FAILED",
                    duration_ms=d1,
                    summary="Requirement analysis failed.",
                    error=str(e),
                )
            )
            automation_log.status = "FAILED"
            automation_log.error = str(e)
            await self.db.commit()
            return PipelineExecutionResponse(
                execution_id=execution_id,
                project_id=analysis.project_id,
                analysis_id=analysis.id,
                status="FAILED",
                stages=stages,
                message=f"Pipeline failed during requirement analysis: {e}",
                total_duration_ms=int((time.monotonic() - pipeline_started) * 1000),
            )

        # ── APPROVAL CHECK ──────────────────────────────────────────────────────
        is_approved = (
            getattr(analysis.status, "value", str(analysis.status)) == "APPROVED"
        )
        if not is_approved and auto_approve_requirements:
            analysis = await self.requirements_service.approve_analysis(user_id, analysis.id)
            is_approved = True

        if not is_approved:
            stages.append(
                PipelineStageLog(
                    stage_name="Task Planner",
                    status="AWAITING_APPROVAL",
                    duration_ms=0,
                    summary="Awaiting developer review and approval of requirements before generating implementation plan.",
                )
            )
            stages.append(
                PipelineStageLog(
                    stage_name="Proposal Generator",
                    status="AWAITING_APPROVAL",
                    duration_ms=0,
                    summary="Awaiting approved requirements before proposal drafting.",
                )
            )
            automation_log.status = "AWAITING_APPROVAL"
            automation_log.result_data = {
                "status": "PENDING_REQUIREMENT_APPROVAL",
                "analysis_id": analysis.id,
                "requirements_count": len(analysis.requirements),
            }
            await self.db.commit()
            return PipelineExecutionResponse(
                execution_id=execution_id,
                project_id=analysis.project_id,
                analysis_id=analysis.id,
                status="PENDING_REQUIREMENT_APPROVAL",
                stages=stages,
                requirements_count=len(analysis.requirements),
                unresolved_questions_count=0,
                message="Requirements are ready for review. Approve them to unlock task planning and proposal drafting.",
                total_duration_ms=int((time.monotonic() - pipeline_started) * 1000),
            )

        # ── STAGE 2: Task Planner Agent ─────────────────────────────────────────
        t1 = time.monotonic()
        planned_tasks_count = 0
        created_tasks_count = 0
        try:
            task_plan = await self.requirements_service.generate_task_plan(user_id, analysis.id)
            planned_tasks_count = len(task_plan.proposed_tasks)

            if auto_create_tasks and task_plan.proposed_tasks:
                approve_dto = ApproveTaskPlanRequest(selected_tasks=task_plan.proposed_tasks)
                res = await self.requirements_service.approve_task_plan(user_id, analysis.id, approve_dto)
                created_tasks_count = res.created_tasks_count

            d2 = int((time.monotonic() - t1) * 1000)
            stages.append(
                PipelineStageLog(
                    stage_name="Task Planner",
                    status="COMPLETED",
                    duration_ms=d2,
                    summary=(
                        f"Generated plan with {planned_tasks_count} tasks"
                        + (f" ({created_tasks_count} persisted with traceability)" if auto_create_tasks else " (draft plan ready for review).")
                    ),
                )
            )
        except Exception as e:
            logger.exception("Task Planner failed")
            d2 = int((time.monotonic() - t1) * 1000)
            stages.append(
                PipelineStageLog(
                    stage_name="Task Planner",
                    status="FAILED",
                    duration_ms=d2,
                    summary="Task planning failed.",
                    error=str(e),
                )
            )

        # ── STAGE 3: Proposal Generator Agent ───────────────────────────────────
        t2 = time.monotonic()
        proposal_id: Optional[str] = None
        if auto_create_proposal:
            try:
                # Check for existing proposal for this analysis to prevent duplicate writes on retry
                stmt = select(Proposal).where(
                    Proposal.analysis_id == analysis.id, Proposal.user_id == user_id
                )
                res = await self.db.execute(stmt)
                existing_prop = res.scalar_one_or_none()

                if existing_prop:
                    proposal_id = str(existing_prop.id)
                    d3 = int((time.monotonic() - t2) * 1000)
                    stages.append(
                        PipelineStageLog(
                            stage_name="Proposal Generator",
                            status="COMPLETED",
                            duration_ms=d3,
                            summary=f"Reused existing proposal draft (ID: {proposal_id}) to prevent duplicate write.",
                        )
                    )
                else:
                    prop_req = AIGenerateProposalRequest(
                        project_id=analysis.project_id,
                        analysis_id=analysis.id,
                        additional_notes="Generated via Multi-Agent Delivery Pipeline",
                    )
                    prop = await self.proposal_service.ai_generate_proposal(user_id, prop_req)
                    proposal_id = str(prop.id)
                    d3 = int((time.monotonic() - t2) * 1000)
                    stages.append(
                        PipelineStageLog(
                            stage_name="Proposal Generator",
                            status="COMPLETED",
                            duration_ms=d3,
                            summary=f"Created structured proposal draft (ID: {proposal_id}) with scope, line items, and terms.",
                        )
                    )
            except Exception as e:
                logger.exception("Proposal Generator failed")
                d3 = int((time.monotonic() - t2) * 1000)
                stages.append(
                    PipelineStageLog(
                        stage_name="Proposal Generator",
                        status="FAILED",
                        duration_ms=d3,
                        summary="Proposal generation failed.",
                        error=str(e),
                    )
                )

        # Determine overall pipeline status
        has_failures = any(s.status == "FAILED" for s in stages)
        final_status = "PARTIAL_SUCCESS" if has_failures else "SUCCESS"

        automation_log.status = final_status
        automation_log.result_data = {
            "status": final_status,
            "analysis_id": analysis.id,
            "requirements_count": len(analysis.requirements),
            "planned_tasks_count": planned_tasks_count,
            "created_tasks_count": created_tasks_count,
            "proposal_id": proposal_id,
        }
        await self.db.commit()

        total_ms = int((time.monotonic() - pipeline_started) * 1000)
        return PipelineExecutionResponse(
            execution_id=execution_id,
            project_id=analysis.project_id,
            analysis_id=analysis.id,
            status=final_status,
            stages=stages,
            requirements_count=len(analysis.requirements),
            unresolved_questions_count=0,
            planned_tasks_count=planned_tasks_count,
            created_tasks_count=created_tasks_count,
            proposal_id=proposal_id,
            message="Multi-agent pipeline completed successfully. All artifacts created and ready for review.",
            total_duration_ms=total_ms,
        )

