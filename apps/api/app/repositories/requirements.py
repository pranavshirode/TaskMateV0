"""Repositories for Requirements Analysis and Traceability."""
from __future__ import annotations

from typing import Any
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirements import (
    RequirementsAnalysis,
    Requirement,
    ClarificationQuestion,
    RequirementAssumption,
    RequirementRisk,
    AnalysisRevision,
    RequirementTaskLink,
)
from app.models.enums import AnalysisStatus, ClarificationStatus, RequirementStatus
from app.repositories.base import BaseRepository


class RequirementsAnalysisRepository(BaseRepository[RequirementsAnalysis]):
    def __init__(self, session: AsyncSession):
        super().__init__(RequirementsAnalysis, session)

    async def get_by_id_with_relations(self, id: str, user_id: str | None = None) -> RequirementsAnalysis | None:
        stmt = (
            select(RequirementsAnalysis)
            .where(RequirementsAnalysis.id == id)
            .options(
                selectinload(RequirementsAnalysis.requirements).selectinload(Requirement.task_links).selectinload(RequirementTaskLink.task),
                selectinload(RequirementsAnalysis.questions),
                selectinload(RequirementsAnalysis.assumptions),
                selectinload(RequirementsAnalysis.risks),
                selectinload(RequirementsAnalysis.revisions),
            )
        )
        if user_id:
            stmt = stmt.where(RequirementsAnalysis.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str, user_id: str) -> list[RequirementsAnalysis]:
        stmt = (
            select(RequirementsAnalysis)
            .where(
                and_(
                    RequirementsAnalysis.project_id == project_id,
                    RequirementsAnalysis.user_id == user_id,
                )
            )
            .options(
                selectinload(RequirementsAnalysis.requirements),
                selectinload(RequirementsAnalysis.questions),
            )
            .order_by(RequirementsAnalysis.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: str) -> list[RequirementsAnalysis]:
        stmt = (
            select(RequirementsAnalysis)
            .where(RequirementsAnalysis.user_id == user_id)
            .options(
                selectinload(RequirementsAnalysis.requirements),
                selectinload(RequirementsAnalysis.questions),
            )
            .order_by(RequirementsAnalysis.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RequirementRepository(BaseRepository[Requirement]):
    def __init__(self, session: AsyncSession):
        super().__init__(Requirement, session)

    async def get_by_id_with_links(self, id: str) -> Requirement | None:
        stmt = (
            select(Requirement)
            .where(Requirement.id == id)
            .options(
                selectinload(Requirement.task_links).selectinload(RequirementTaskLink.task)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_analysis(self, analysis_id: str) -> list[Requirement]:
        stmt = (
            select(Requirement)
            .where(Requirement.analysis_id == analysis_id)
            .options(
                selectinload(Requirement.task_links).selectinload(RequirementTaskLink.task)
            )
            .order_by(Requirement.key.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ClarificationQuestionRepository(BaseRepository[ClarificationQuestion]):
    def __init__(self, session: AsyncSession):
        super().__init__(ClarificationQuestion, session)

    async def list_by_analysis(self, analysis_id: str) -> list[ClarificationQuestion]:
        stmt = (
            select(ClarificationQuestion)
            .where(ClarificationQuestion.analysis_id == analysis_id)
            .order_by(ClarificationQuestion.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_unresolved_by_user(self, user_id: str) -> int:
        stmt = (
            select(func.count(ClarificationQuestion.id))
            .join(RequirementsAnalysis, ClarificationQuestion.analysis_id == RequirementsAnalysis.id)
            .where(
                and_(
                    RequirementsAnalysis.user_id == user_id,
                    ClarificationQuestion.status == ClarificationStatus.UNRESOLVED,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0


class RequirementTaskLinkRepository(BaseRepository[RequirementTaskLink]):
    def __init__(self, session: AsyncSession):
        super().__init__(RequirementTaskLink, session)

    async def get_by_pair(self, requirement_id: str, task_id: str) -> RequirementTaskLink | None:
        stmt = select(RequirementTaskLink).where(
            and_(
                RequirementTaskLink.requirement_id == requirement_id,
                RequirementTaskLink.task_id == task_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_requirement(self, requirement_id: str) -> list[RequirementTaskLink]:
        stmt = (
            select(RequirementTaskLink)
            .where(RequirementTaskLink.requirement_id == requirement_id)
            .options(selectinload(RequirementTaskLink.task))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_task(self, task_id: str) -> list[RequirementTaskLink]:
        stmt = (
            select(RequirementTaskLink)
            .where(RequirementTaskLink.task_id == task_id)
            .options(selectinload(RequirementTaskLink.requirement))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_analysis(self, analysis_id: str) -> list[RequirementTaskLink]:
        stmt = (
            select(RequirementTaskLink)
            .join(Requirement, RequirementTaskLink.requirement_id == Requirement.id)
            .where(Requirement.analysis_id == analysis_id)
            .options(
                selectinload(RequirementTaskLink.requirement),
                selectinload(RequirementTaskLink.task),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AnalysisRevisionRepository(BaseRepository[AnalysisRevision]):
    def __init__(self, session: AsyncSession):
        super().__init__(AnalysisRevision, session)

    async def list_by_analysis(self, analysis_id: str) -> list[AnalysisRevision]:
        stmt = (
            select(AnalysisRevision)
            .where(AnalysisRevision.analysis_id == analysis_id)
            .order_by(AnalysisRevision.revision_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

