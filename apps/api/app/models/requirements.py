"""Sprint 4 Data Models: Requirements Analysis, Traceability, Project Memory, Client Requests, and Automation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import (
    AnalysisStatus,
    AutomationType,
    ClarificationStatus,
    ClientRequestStatus,
    ClientRequestType,
    ContextCategory,
    RequirementCategory,
    RequirementStatus,
)


class RequirementsAnalysis(Base):
    """A requirements analysis session for a project."""

    __tablename__ = "requirements_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    brief: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    repository_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus), default=AnalysisStatus.DRAFT, nullable=False, index=True
    )
    overview_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    technical_constraints: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    non_functional_requirements: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    requirements: Mapped[list[Requirement]] = relationship(
        "Requirement", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    questions: Mapped[list[ClarificationQuestion]] = relationship(
        "ClarificationQuestion", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    assumptions: Mapped[list[RequirementAssumption]] = relationship(
        "RequirementAssumption", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    risks: Mapped[list[RequirementRisk]] = relationship(
        "RequirementRisk", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    revisions: Mapped[list[AnalysisRevision]] = relationship(
        "AnalysisRevision", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )


class Requirement(Base):
    """An individual structured functional or non-functional requirement."""

    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. "FR-1", "NFR-1"
    category: Mapped[RequirementCategory] = mapped_column(
        SAEnum(RequirementCategory), default=RequirementCategory.FUNCTIONAL, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    status: Mapped[RequirementStatus] = mapped_column(
        SAEnum(RequirementStatus), default=RequirementStatus.PROPOSED, nullable=False, index=True
    )
    acceptance_criteria: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    open_questions: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    analysis: Mapped[RequirementsAnalysis] = relationship("RequirementsAnalysis", back_populates="requirements")
    task_links: Mapped[list[RequirementTaskLink]] = relationship(
        "RequirementTaskLink", back_populates="requirement", cascade="all, delete-orphan", lazy="selectin"
    )


class ClarificationQuestion(Base):
    """A clarifying question generated by the AI to resolve ambiguity in the brief."""

    __tablename__ = "clarification_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_key: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Q-1"
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ClarificationStatus] = mapped_column(
        SAEnum(ClarificationStatus), default=ClarificationStatus.UNRESOLVED, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analysis: Mapped[RequirementsAnalysis] = relationship("RequirementsAnalysis", back_populates="questions")


class RequirementAssumption(Base):
    """An assumption recorded separately from confirmed requirements."""

    __tablename__ = "requirement_assumptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="UNCONFIRMED", nullable=False
    )  # UNCONFIRMED, CONFIRMED, REFUTED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis: Mapped[RequirementsAnalysis] = relationship("RequirementsAnalysis", back_populates="assumptions")


class RequirementRisk(Base):
    """An identified implementation risk or dependency."""

    __tablename__ = "requirement_risks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_type: Mapped[str] = mapped_column(
        String(100), default="TECHNICAL", nullable=False
    )  # TECHNICAL, DEPENDENCY, SCHEDULE, SECURITY
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis: Mapped[RequirementsAnalysis] = relationship("RequirementsAnalysis", back_populates="risks")


class AnalysisRevision(Base):
    """Auditable snapshot of a requirements analysis version."""

    __tablename__ = "analysis_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis: Mapped[RequirementsAnalysis] = relationship("RequirementsAnalysis", back_populates="revisions")


class RequirementTaskLink(Base):
    """Bidirectional traceability link between a requirement and a persisted task."""

    __tablename__ = "requirement_task_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    requirement: Mapped[Requirement] = relationship("Requirement", back_populates="task_links")
    task: Mapped[Task] = relationship("Task", foreign_keys=[task_id], lazy="selectin")


class ProjectContextNote(Base):
    """Explicitly recorded project context, architectural decisions, and constraints for AI memory."""

    __tablename__ = "project_context_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ContextCategory] = mapped_column(
        SAEnum(ContextCategory), default=ContextCategory.DECISION, nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(100), default="MANUAL", nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    superseded_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ClientRequest(Base):
    """An incoming client brief, email, meeting note, or change request."""

    __tablename__ = "client_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    request_type: Mapped[ClientRequestType] = mapped_column(
        SAEnum(ClientRequestType), default=ClientRequestType.NEW_FEATURE, nullable=False, index=True
    )
    status: Mapped[ClientRequestStatus] = mapped_column(
        SAEnum(ClientRequestStatus), default=ClientRequestStatus.SUBMITTED, nullable=False, index=True
    )
    impact_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    analysis_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AutomationExecution(Base):
    """Observable record of an executed automation workflow."""

    __tablename__ = "automation_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    automation_type: Mapped[AutomationType] = mapped_column(SAEnum(AutomationType), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="SUCCESS", nullable=False, index=True
    )  # SUCCESS, FAILED, PENDING
    trigger: Mapped[str] = mapped_column(String(100), default="USER_TRIGGERED", nullable=False)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
