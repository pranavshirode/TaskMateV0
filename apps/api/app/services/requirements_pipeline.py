"""Requirements Analysis Service and Pipeline."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.errors import AIError
from app.ai.extractors.requirements_analyzer import (
    validate_and_sanitize_requirements_data,
)
from app.ai.prompts.requirements import (
    REQUIREMENTS_ANALYSIS_SYSTEM_PROMPT,
    TASK_PLANNING_SYSTEM_PROMPT,
)
from app.ai.providers.base import AIMessage, BaseAIProvider
from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.enums import (
    AnalysisStatus,
    AutomationType,
    ClarificationStatus,
    RequirementCategory,
    RequirementStatus,
    TaskPriority,
    TaskStatus,
)
from app.models.requirements import (
    AnalysisRevision,
    AutomationExecution,
    ClarificationQuestion,
    Requirement,
    RequirementAssumption,
    RequirementRisk,
    RequirementsAnalysis,
    RequirementTaskLink,
)
from app.repositories.project import ProjectRepository
from app.repositories.project_context import ProjectContextNoteRepository
from app.repositories.requirements import (
    AnalysisRevisionRepository,
    ClarificationQuestionRepository,
    RequirementRepository,
    RequirementsAnalysisRepository,
    RequirementTaskLinkRepository,
)
from app.schemas.requirements import (
    ApproveTaskPlanRequest,
    ApproveTaskPlanResponse,
    CreatedTaskResult,
    GenerateTaskPlanResponse,
    RequirementsAnalysisCreate,
    RequirementTraceabilityItem,
    RequirementUpdate,
    TaskPlanItem,
    TaskTraceabilityInfo,
    TraceabilityResponse,
)
from app.schemas.task import TaskCreate
from app.services.task import TaskService

logger = logging.getLogger(__name__)


class RequirementsService:
    def __init__(
        self,
        db: AsyncSession,
        ai_provider: BaseAIProvider,
        task_service: TaskService,
    ):
        self.db = db
        self.ai_provider = ai_provider
        self.task_service = task_service
        self.analysis_repo = RequirementsAnalysisRepository(db)
        self.req_repo = RequirementRepository(db)
        self.question_repo = ClarificationQuestionRepository(db)
        self.link_repo = RequirementTaskLinkRepository(db)
        self.revision_repo = AnalysisRevisionRepository(db)
        self.project_repo = ProjectRepository(db)
        self.context_repo = ProjectContextNoteRepository(db)

    async def _verify_project_ownership(self, user_id: str, project_id: str) -> Any:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by authenticated user")
        return project

    async def create_analysis(self, user_id: str, data: RequirementsAnalysisCreate) -> RequirementsAnalysis:
        await self._verify_project_ownership(user_id, data.project_id)

        analysis = RequirementsAnalysis(
            project_id=data.project_id,
            user_id=user_id,
            title=data.title.strip(),
            brief=data.brief.strip(),
            desired_outcome=data.desired_outcome.strip() if data.desired_outcome else None,
            constraints=data.constraints.strip() if data.constraints else None,
            deadline=data.deadline.strip() if data.deadline else None,
            repository_id=data.repository_id,
            status=AnalysisStatus.DRAFT,
            version=1,
        )
        created = await self.analysis_repo.create(analysis)
        return await self.analysis_repo.get_by_id_with_relations(created.id, user_id=user_id)  # type: ignore

    async def get_analysis(self, user_id: str, analysis_id: str) -> RequirementsAnalysis:
        analysis = await self.analysis_repo.get_by_id_with_relations(analysis_id, user_id=user_id)
        if not analysis:
            raise NotFoundError("Requirements analysis not found")
        return analysis

    async def list_by_project(self, user_id: str, project_id: str) -> list[RequirementsAnalysis]:
        await self._verify_project_ownership(user_id, project_id)
        return await self.analysis_repo.list_by_project(project_id, user_id)

    async def analyze(self, user_id: str, analysis_id: str) -> RequirementsAnalysis:
        analysis = await self.get_analysis(user_id, analysis_id)
        project = await self.project_repo.get_by_id(analysis.project_id)

        # Retrieve explicit project context memory
        context_notes = await self.context_repo.get_active_notes_for_context(
            project_id=analysis.project_id, user_id=user_id, limit=10
        )
        context_str = "\n".join(
            f"- [{note.category}] {note.title}: {note.content} (Confirmed: {note.is_confirmed})"
            for note in context_notes
        )

        # Retrieve existing answers if this is a re-analysis
        answered_q_str = ""
        if analysis.questions:
            answered_qs = [
                f"Q ({q.question_key}): {q.question}\nA: {q.answer}"
                for q in analysis.questions
                if q.answer and q.status == ClarificationStatus.RESOLVED
            ]
            if answered_qs:
                answered_q_str = "\n\nResolved Clarifications:\n" + "\n\n".join(answered_qs)

        user_prompt = f"""Project: {project.name if project else "Unknown"}
Project Description: {project.description if project and project.description else "None"}
Analysis Title: {analysis.title}
Client Brief:
{analysis.brief}

Desired Outcome: {analysis.desired_outcome or "Not specified"}
Constraints: {analysis.constraints or "Not specified"}
Deadline: {analysis.deadline or "Not specified"}

Project Context & Decisions:
{context_str or "No existing context notes."}
{answered_q_str}

Analyze this client brief and return the complete requirements specification in JSON.
"""

        messages = [
            AIMessage(role="system", content=REQUIREMENTS_ANALYSIS_SYSTEM_PROMPT),
            AIMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self.ai_provider.generate(
                messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except AIError as e:
            logger.warning("Requirements analysis provider error: %s", e)
            raise AppError(503, "AI_UNAVAILABLE", "The AI service is unavailable right now. Please try again.") from e

        # Invalid output is reported, never replaced with template requirements: the developer must not
        # mistake generic text for an analysis of their client's brief.
        try:
            parsed = validate_and_sanitize_requirements_data(
                parsed=json.loads(response.content),
                brief=analysis.brief,
                project_name=project.name if project else "",
                title=analysis.title,
                desired_outcome=analysis.desired_outcome or "",
                constraints=analysis.constraints or "",
            )
        except (ValueError, TypeError) as e:
            logger.warning("Requirements analysis returned invalid JSON: %s", e)
            raise AppError(
                502, "AI_INVALID_RESPONSE", "The AI returned an unreadable analysis. Nothing was saved; please retry."
            ) from e

        # Store overview & constraints
        analysis.overview_data = parsed.get("overview", {})
        analysis.technical_constraints = parsed.get("technical_constraints", [])
        analysis.non_functional_requirements = parsed.get("non_functional_requirements", [])

        # Preserve previously resolved question answers
        resolved_answers = {
            q.question_key: q.answer
            for q in analysis.questions
            if q.answer and q.status == ClarificationStatus.RESOLVED
        }

        # Clear existing transient collections for new version
        analysis.requirements.clear()
        analysis.questions.clear()
        analysis.assumptions.clear()
        analysis.risks.clear()

        # Add Functional Requirements
        for i, fr in enumerate(parsed.get("functional_requirements", []), start=1):
            key = fr.get("key") or f"FR-{i}"
            analysis.requirements.append(
                Requirement(
                    analysis_id=analysis.id,
                    key=key,
                    category=RequirementCategory.FUNCTIONAL,
                    title=fr.get("title", f"Requirement {i}"),
                    description=fr.get("description", ""),
                    priority=fr.get("priority", "MEDIUM"),
                    status=RequirementStatus.PROPOSED,
                    acceptance_criteria=fr.get("acceptance_criteria", []),
                    dependencies=fr.get("dependencies", []),
                    open_questions=fr.get("open_questions", []),
                    source=fr.get("source"),
                )
            )

        # Add Non-functional Requirements
        for j, nfr in enumerate(parsed.get("non_functional_requirements", []), start=1):
            key = nfr.get("key") or f"NFR-{j}"
            analysis.requirements.append(
                Requirement(
                    analysis_id=analysis.id,
                    key=key,
                    category=RequirementCategory.NON_FUNCTIONAL,
                    title=nfr.get("title", f"Non-Functional {j}"),
                    description=nfr.get("description", ""),
                    priority=nfr.get("priority", "MEDIUM"),
                    status=RequirementStatus.PROPOSED,
                    acceptance_criteria=[],
                    dependencies=[],
                    open_questions=[],
                    source=nfr.get("source"),
                )
            )

        # Add Clarification Questions
        has_unresolved = False
        for k, q in enumerate(parsed.get("clarification_questions", []), start=1):
            q_key = q.get("question_key") or f"Q-{k}"
            existing_ans = resolved_answers.get(q_key)
            status = ClarificationStatus.RESOLVED if existing_ans else ClarificationStatus.UNRESOLVED
            if status == ClarificationStatus.UNRESOLVED:
                has_unresolved = True
            analysis.questions.append(
                ClarificationQuestion(
                    analysis_id=analysis.id,
                    question_key=q_key,
                    question=q.get("question", ""),
                    reason=q.get("reason"),
                    context_topic=q.get("context_topic"),
                    answer=existing_ans,
                    status=status,
                )
            )

        # Add Assumptions
        for asm in parsed.get("assumptions", []):
            analysis.assumptions.append(
                RequirementAssumption(
                    analysis_id=analysis.id,
                    description=asm.get("description", ""),
                    reason=asm.get("reason"),
                    confidence=asm.get("confidence", "MEDIUM"),
                    status="UNCONFIRMED",
                )
            )

        # Add Risks
        for rk in parsed.get("risks_and_dependencies", []):
            analysis.risks.append(
                RequirementRisk(
                    analysis_id=analysis.id,
                    description=rk.get("description", ""),
                    risk_type=rk.get("risk_type", "TECHNICAL"),
                    severity=rk.get("severity", "MEDIUM"),
                    mitigation=rk.get("mitigation"),
                )
            )

        # Update status
        if has_unresolved:
            analysis.status = AnalysisStatus.NEEDS_CLARIFICATION
        else:
            analysis.status = AnalysisStatus.READY_FOR_REVIEW

        analysis.version += 1
        analysis.updated_at = datetime.now(timezone.utc)

        # Create audit revision snapshot
        snapshot = {
            "version": analysis.version,
            "status": analysis.status.value,
            "overview": analysis.overview_data,
            "requirements": [
                {"key": r.key, "title": r.title, "description": r.description, "category": r.category.value}
                for r in analysis.requirements
            ],
            "questions": [
                {"key": q.question_key, "question": q.question, "status": q.status.value, "answer": q.answer}
                for q in analysis.questions
            ],
        }
        revision = AnalysisRevision(
            analysis_id=analysis.id,
            revision_number=analysis.version,
            snapshot_data=snapshot,
            change_summary=f"Analysis regenerated (version {analysis.version})",
        )
        self.db.add(revision)

        await self.analysis_repo.update(analysis)
        return await self.get_analysis(user_id, analysis.id)

    async def answer_question(
        self, user_id: str, analysis_id: str, question_id: str, answer: str
    ) -> ClarificationQuestion:
        analysis = await self.get_analysis(user_id, analysis_id)
        question = await self.question_repo.get_by_id(question_id)
        if not question or question.analysis_id != analysis.id:
            raise NotFoundError("Clarification question not found")

        question.answer = answer.strip()
        question.status = ClarificationStatus.RESOLVED
        question.updated_at = datetime.now(timezone.utc)
        await self.question_repo.update(question)

        # Check if all questions are now resolved
        all_questions = await self.question_repo.list_by_analysis(analysis_id)
        if all(q.status == ClarificationStatus.RESOLVED for q in all_questions):
            analysis.status = AnalysisStatus.READY_FOR_REVIEW
            await self.analysis_repo.update(analysis)

        return question

    async def update_requirement(
        self, user_id: str, analysis_id: str, requirement_id: str, data: RequirementUpdate
    ) -> Requirement:
        analysis = await self.get_analysis(user_id, analysis_id)
        req = await self.req_repo.get_by_id(requirement_id)
        if not req or req.analysis_id != analysis.id:
            raise NotFoundError("Requirement not found")

        if data.title is not None:
            req.title = data.title.strip()
        if data.description is not None:
            req.description = data.description.strip()
        if data.priority is not None:
            req.priority = data.priority
        if data.status is not None:
            try:
                req.status = RequirementStatus(data.status)
            except ValueError as err:
                raise ValidationError(f"Invalid requirement status: {data.status}") from err
        if data.acceptance_criteria is not None:
            req.acceptance_criteria = data.acceptance_criteria
        if data.dependencies is not None:
            req.dependencies = data.dependencies

        req.updated_at = datetime.now(timezone.utc)
        return await self.req_repo.update(req)

    async def approve_analysis(self, user_id: str, analysis_id: str) -> RequirementsAnalysis:
        analysis = await self.get_analysis(user_id, analysis_id)

        # Valid transitions: DRAFT, NEEDS_CLARIFICATION, READY_FOR_REVIEW -> APPROVED
        if analysis.status == AnalysisStatus.ARCHIVED:
            raise ValidationError("Cannot approve an archived requirements analysis")

        analysis.status = AnalysisStatus.APPROVED
        analysis.approved_at = datetime.now(timezone.utc)
        analysis.updated_at = datetime.now(timezone.utc)

        # Confirm all proposed requirements
        for r in analysis.requirements:
            if r.status == RequirementStatus.PROPOSED or r.status == RequirementStatus.NEEDS_CLARIFICATION:
                r.status = RequirementStatus.APPROVED

        await self.analysis_repo.update(analysis)
        return await self.get_analysis(user_id, analysis_id)

    async def archive_analysis(self, user_id: str, analysis_id: str) -> RequirementsAnalysis:
        analysis = await self.get_analysis(user_id, analysis_id)
        analysis.status = AnalysisStatus.ARCHIVED
        analysis.updated_at = datetime.now(timezone.utc)
        await self.analysis_repo.update(analysis)
        return analysis

    async def generate_task_plan(self, user_id: str, analysis_id: str) -> GenerateTaskPlanResponse:
        analysis = await self.get_analysis(user_id, analysis_id)

        # Filter approved/confirmed requirements
        req_list = [
            f"- [{r.key}] ({r.priority}) {r.title}: {r.description}\n  Acceptance criteria: {r.acceptance_criteria}"
            for r in analysis.requirements
            if r.status != RequirementStatus.REJECTED
        ]
        reqs_str = "\n".join(req_list)

        user_prompt = f"""Requirements Analysis: {analysis.title}
Requirements to implement:
{reqs_str}

Technical constraints:
{analysis.technical_constraints}

Create a structured implementation task plan in JSON breaking down these requirements.
"""

        messages = [
            AIMessage(role="system", content=TASK_PLANNING_SYSTEM_PROMPT),
            AIMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self.ai_provider.generate(
                messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except AIError as e:
            raise AppError(503, "AI_UNAVAILABLE", "The AI service is unavailable right now. Please try again.") from e

        try:
            parsed = json.loads(response.content)
            raw_tasks = parsed.get("proposed_tasks", [])
            rationale = parsed.get("rationale", "Proposed task plan derived from approved requirements.")
        except Exception:
            raw_tasks = [
                {
                    "title": f"Implement {r.title}",
                    "description": r.description,
                    "priority": r.priority,
                    "status": "TODO",
                    "linked_requirement_keys": [r.key],
                    "acceptance_criteria": r.acceptance_criteria,
                    "estimated_effort": None,  # no basis for an estimate without the AI plan
                }
                for r in analysis.requirements
            ]
            rationale = "The AI plan could not be read, so this is a simple one-task-per-requirement draft. Review it."

        task_items: list[TaskPlanItem] = []
        for t in raw_tasks:
            task_items.append(
                TaskPlanItem(
                    title=t.get("title", "Implementation Task"),
                    description=t.get("description"),
                    priority=t.get("priority", "MEDIUM"),
                    status=t.get("status", "TODO"),
                    deadline=t.get("deadline"),
                    linked_requirement_keys=t.get("linked_requirement_keys", []),
                    acceptance_criteria=t.get("acceptance_criteria"),
                    estimated_effort=t.get("estimated_effort"),
                )
            )

        return GenerateTaskPlanResponse(
            analysis_id=analysis_id,
            proposed_tasks=task_items,
            rationale=rationale,
            generated_at=datetime.now(timezone.utc),
        )

    async def approve_task_plan(
        self, user_id: str, analysis_id: str, data: ApproveTaskPlanRequest
    ) -> ApproveTaskPlanResponse:
        analysis = await self.get_analysis(user_id, analysis_id)

        # Tasks may only be created from requirements the developer has approved.
        if analysis.status != AnalysisStatus.APPROVED:
            raise ConflictError(
                "Approve the requirements analysis before creating tasks from it.",
                code="ANALYSIS_NOT_APPROVED",
            )

        if not data.selected_tasks:
            raise ValidationError("No tasks were selected for creation")

        # Map requirements by key for easy linking
        req_by_key = {r.key: r for r in analysis.requirements}

        created_tasks: list[CreatedTaskResult] = []
        links_created_count = 0

        existing_tasks, _ = await self.task_service.task_repo.list_by_user(
            user_id=user_id, project_id=analysis.project_id, page=1, page_size=500
        )
        existing_titles = {t.title: t.id for t in existing_tasks}

        for item in data.selected_tasks:
            # Check for existing duplicate task
            if item.title in existing_titles:
                task_id = existing_titles[item.title]
                created_tasks.append(
                    CreatedTaskResult(
                        id=task_id,
                        title=item.title,
                        priority=item.priority,
                        status="TODO",
                        linked_requirements=item.linked_requirement_keys,
                    )
                )
                # Ensure links exist
                for key in item.linked_requirement_keys:
                    req = req_by_key.get(key)
                    if req:
                        existing_link = await self.link_repo.get_by_pair(req.id, task_id)
                        if not existing_link:
                            link = RequirementTaskLink(requirement_id=req.id, task_id=task_id)
                            await self.link_repo.create(link)
                            links_created_count += 1
                continue

            # Parse priority
            try:
                task_prio = TaskPriority(item.priority.upper())
            except Exception:
                task_prio = TaskPriority.MEDIUM

            # Build description with acceptance criteria
            desc = item.description or ""
            if item.acceptance_criteria:
                desc += "\n\nAcceptance Criteria:\n" + "\n".join(f"- {c}" for c in item.acceptance_criteria)
            if item.linked_requirement_keys:
                desc += f"\n\nLinked Requirements: {', '.join(item.linked_requirement_keys)}"

            task_in = TaskCreate(
                title=item.title.strip(),
                description=desc.strip(),
                priority=task_prio,
                status=TaskStatus.TODO,
                project_id=analysis.project_id,
                labels=["sprint-4", "requirement-task"],
            )

            # Create task using standard TaskService
            created_task = await self.task_service.create(user_id, task_in)
            existing_titles[created_task.title] = created_task.id

            created_tasks.append(
                CreatedTaskResult(
                    id=created_task.id,
                    title=created_task.title,
                    priority=created_task.priority.value,
                    status=created_task.status.value,
                    linked_requirements=item.linked_requirement_keys,
                )
            )

            # Create RequirementTaskLink records
            for key in item.linked_requirement_keys:
                req = req_by_key.get(key)
                if req:
                    link = RequirementTaskLink(
                        requirement_id=req.id,
                        task_id=created_task.id,
                    )
                    await self.link_repo.create(link)
                    links_created_count += 1

        # Record automation execution log
        automation = AutomationExecution(
            user_id=user_id,
            project_id=analysis.project_id,
            automation_type=AutomationType.APPROVED_REQUIREMENTS_TO_TASKS,
            status="SUCCESS",
            trigger="USER_TRIGGERED",
            result_data={
                "analysis_id": analysis.id,
                "tasks_created_count": len(created_tasks),
                "links_created_count": links_created_count,
            },
        )
        self.db.add(automation)
        await self.db.commit()

        return ApproveTaskPlanResponse(
            analysis_id=analysis.id,
            created_tasks_count=len(created_tasks),
            tasks=created_tasks,
            traceability_links_created=links_created_count,
            message=f"Successfully created {len(created_tasks)} tasks with {links_created_count} traceability links.",
        )

    async def get_traceability(self, user_id: str, analysis_id: str) -> TraceabilityResponse:
        analysis = await self.get_analysis(user_id, analysis_id)

        items: list[RequirementTraceabilityItem] = []
        total_reqs = len(analysis.requirements)
        implemented_count = 0

        for r in analysis.requirements:
            linked_tasks: list[TaskTraceabilityInfo] = []
            completed_tasks = 0

            for link in r.task_links:
                if link.task:
                    linked_tasks.append(
                        TaskTraceabilityInfo(
                            id=link.task.id,
                            title=link.task.title,
                            status=link.task.status.value,
                            priority=link.task.priority.value,
                        )
                    )
                    if link.task.status == TaskStatus.COMPLETED:
                        completed_tasks += 1

            total_linked = len(linked_tasks)
            progress = (completed_tasks / total_linked * 100.0) if total_linked > 0 else 0.0

            # Deterministic requirement status update based on actual task state
            if total_linked > 0 and completed_tasks == total_linked:
                if r.status != RequirementStatus.IMPLEMENTED:
                    r.status = RequirementStatus.IMPLEMENTED
                    await self.req_repo.update(r)
                implemented_count += 1

            items.append(
                RequirementTraceabilityItem(
                    requirement_id=r.id,
                    key=r.key,
                    title=r.title,
                    status=r.status.value,
                    priority=r.priority,
                    progress_percent=round(progress, 1),
                    linked_tasks=linked_tasks,
                )
            )

        overall_progress = (implemented_count / total_reqs * 100.0) if total_reqs > 0 else 0.0

        return TraceabilityResponse(
            analysis_id=analysis.id,
            total_requirements=total_reqs,
            implemented_requirements=implemented_count,
            unimplemented_requirements=total_reqs - implemented_count,
            overall_progress_percent=round(overall_progress, 1),
            items=items,
        )
