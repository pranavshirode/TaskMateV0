"""Workflow Automation Service for Daily Summaries, Consistency, and Audit Logging."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError
from app.models.enums import (
    AutomationType,
    ClarificationStatus,
    RequirementStatus,
    TaskStatus,
)
from app.models.requirements import (
    AutomationExecution,
)
from app.repositories.automation import AutomationExecutionRepository
from app.repositories.project import ProjectRepository
from app.repositories.requirements import (
    ClarificationQuestionRepository,
    RequirementRepository,
    RequirementsAnalysisRepository,
)
from app.repositories.task import TaskRepository
from app.schemas.requirements import DailyProjectSummaryResponse


class WorkflowAutomationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exec_repo = AutomationExecutionRepository(db)
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.analysis_repo = RequirementsAnalysisRepository(db)
        self.req_repo = RequirementRepository(db)
        self.question_repo = ClarificationQuestionRepository(db)

    async def generate_daily_project_summary(self, user_id: str, project_id: str) -> DailyProjectSummaryResponse:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by user")

        now = datetime.now(timezone.utc)
        today = now.date()
        yesterday = today - timedelta(days=1)
        next_week = today + timedelta(days=7)

        # 1. Fetch real tasks for this project
        tasks, _ = await self.task_repo.list_by_user(user_id=user_id, project_id=project_id, page=1, page_size=100)

        completed_recently = []
        in_progress = []
        due_soon = []
        overdue = []
        active_blockers = []

        for t in tasks:
            t_dict = {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.value,
                "due_date": str(t.due_date) if t.due_date else None,
            }
            if t.status == TaskStatus.COMPLETED and t.updated_at and t.updated_at.date() >= yesterday:
                completed_recently.append(t_dict)
            elif t.status == TaskStatus.IN_PROGRESS:
                in_progress.append(t_dict)
            elif t.status == TaskStatus.BLOCKED:
                active_blockers.append(t_dict)

            if t.due_date and t.status != TaskStatus.COMPLETED:
                if t.due_date < today:
                    overdue.append(t_dict)
                elif today <= t.due_date <= next_week:
                    due_soon.append(t_dict)

        # 2. Fetch requirements and clarification questions
        analyses = await self.analysis_repo.list_by_project(project_id, user_id)
        unresolved_reqs = []
        pending_questions = []

        for a in analyses:
            for r in a.requirements:
                if r.status not in (
                    RequirementStatus.APPROVED,
                    RequirementStatus.IMPLEMENTED,
                    RequirementStatus.REJECTED,
                ):
                    unresolved_reqs.append(
                        {
                            "id": r.id,
                            "key": r.key,
                            "title": r.title,
                            "status": r.status.value,
                            "priority": r.priority,
                        }
                    )
            for q in a.questions:
                if q.status == ClarificationStatus.UNRESOLVED:
                    pending_questions.append(
                        {
                            "id": q.id,
                            "question_key": q.question_key,
                            "question": q.question,
                            "reason": q.reason,
                        }
                    )

        # Build natural summary text
        summary_text = (
            f"Project '{project.name}' Daily Summary ({today.isoformat()}):\n"
            f"- Tasks completed recently: {len(completed_recently)}\n"
            f"- Tasks in progress: {len(in_progress)}\n"
            f"- Tasks due soon: {len(due_soon)}\n"
            f"- Overdue tasks: {len(overdue)}\n"
            f"- Active blockers: {len(active_blockers)}\n"
            f"- Unresolved requirements: {len(unresolved_reqs)}\n"
            f"- Pending clarification questions: {len(pending_questions)}"
        )

        # Record automation execution log
        automation = AutomationExecution(
            user_id=user_id,
            project_id=project_id,
            automation_type=AutomationType.DAILY_PROJECT_SUMMARY,
            status="SUCCESS",
            trigger="ON_DEMAND",
            result_data={
                "completed_count": len(completed_recently),
                "in_progress_count": len(in_progress),
                "overdue_count": len(overdue),
                "unresolved_reqs_count": len(unresolved_reqs),
            },
        )
        self.db.add(automation)
        await self.db.commit()

        return DailyProjectSummaryResponse(
            project_id=project_id,
            project_name=project.name,
            generated_at=now,
            completed_recently=completed_recently,
            in_progress=in_progress,
            due_soon=due_soon,
            overdue=overdue,
            unresolved_requirements=unresolved_reqs,
            pending_clarification_questions=pending_questions,
            active_blockers=active_blockers,
            summary_text=summary_text,
        )

    async def sync_task_consistency(self, user_id: str, project_id: str) -> dict[str, Any]:
        """Verify and update requirement statuses based on actual linked task completion."""
        analyses = await self.analysis_repo.list_by_project(project_id, user_id)
        updated_requirements = 0

        for a in analyses:
            for r in a.requirements:
                if r.task_links:
                    all_completed = all(link.task and link.task.status == TaskStatus.COMPLETED for link in r.task_links)
                    if all_completed and r.status != RequirementStatus.IMPLEMENTED:
                        r.status = RequirementStatus.IMPLEMENTED
                        await self.req_repo.update(r)
                        updated_requirements += 1

        return {
            "project_id": project_id,
            "updated_requirements_count": updated_requirements,
            "status": "CONSISTENT",
        }

    async def list_executions(self, user_id: str, project_id: str | None = None) -> list[AutomationExecution]:
        if project_id:
            return await self.exec_repo.list_by_project(project_id, user_id)
        return await self.exec_repo.list_by_user(user_id)
