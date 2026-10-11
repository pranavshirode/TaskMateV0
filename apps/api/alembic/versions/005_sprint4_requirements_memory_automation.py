"""Sprint 4: Requirements Analysis, Traceability, Project Memory, Client Requests, Automation

Revision ID: 005_sprint4
Revises: 004_sprint3
Create Date: 2026-10-11 22:30:00.000000
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "005_sprint4"
down_revision: str = "004_sprint3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. requirements_analyses
    op.create_table(
        "requirements_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("desired_outcome", sa.Text(), nullable=True),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("deadline", sa.String(100), nullable=True),
        sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("overview_data", sa.JSON(), nullable=True),
        sa.Column("technical_constraints", sa.JSON(), nullable=True),
        sa.Column("non_functional_requirements", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_requirements_analyses_project_id", "requirements_analyses", ["project_id"])
    op.create_index("ix_requirements_analyses_user_id", "requirements_analyses", ["user_id"])
    op.create_index("ix_requirements_analyses_status", "requirements_analyses", ["status"])

    # 2. requirements
    op.create_table(
        "requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="FUNCTIONAL"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(50), nullable=False, server_default="PROPOSED"),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("open_questions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_requirements_analysis_id", "requirements", ["analysis_id"])
    op.create_index("ix_requirements_key", "requirements", ["key"])
    op.create_index("ix_requirements_status", "requirements", ["status"])

    # 3. clarification_questions
    op.create_table(
        "clarification_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_key", sa.String(50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("context_topic", sa.String(255), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="UNRESOLVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_clarification_questions_analysis_id", "clarification_questions", ["analysis_id"])
    op.create_index("ix_clarification_questions_status", "clarification_questions", ["status"])

    # 4. requirement_assumptions
    op.create_table(
        "requirement_assumptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(50), nullable=False, server_default="UNCONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_requirement_assumptions_analysis_id", "requirement_assumptions", ["analysis_id"])

    # 5. requirement_risks
    op.create_table(
        "requirement_risks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_type", sa.String(100), nullable=False, server_default="TECHNICAL"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column("mitigation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_requirement_risks_analysis_id", "requirement_risks", ["analysis_id"])

    # 6. analysis_revisions
    op.create_table(
        "analysis_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_data", sa.JSON(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_revisions_analysis_id", "analysis_revisions", ["analysis_id"])

    # 7. requirement_task_links
    op.create_table(
        "requirement_task_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("requirement_id", sa.String(36), sa.ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("requirement_id", "task_id", name="uq_requirement_task_link"),
    )
    op.create_index("ix_requirement_task_links_requirement_id", "requirement_task_links", ["requirement_id"])
    op.create_index("ix_requirement_task_links_task_id", "requirement_task_links", ["task_id"])

    # 8. project_context_notes
    op.create_table(
        "project_context_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="DECISION"),
        sa.Column("source", sa.String(100), nullable=False, server_default="MANUAL"),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superseded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("superseded_by_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_project_context_notes_project_id", "project_context_notes", ["project_id"])
    op.create_index("ix_project_context_notes_user_id", "project_context_notes", ["user_id"])
    op.create_index("ix_project_context_notes_is_superseded", "project_context_notes", ["is_superseded"])

    # 9. client_requests
    op.create_table(
        "client_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("request_type", sa.String(50), nullable=False, server_default="NEW_FEATURE"),
        sa.Column("status", sa.String(50), nullable=False, server_default="SUBMITTED"),
        sa.Column("impact_summary", sa.JSON(), nullable=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("requirements_analyses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_requests_project_id", "client_requests", ["project_id"])
    op.create_index("ix_client_requests_user_id", "client_requests", ["user_id"])
    op.create_index("ix_client_requests_status", "client_requests", ["status"])

    # 10. automation_executions
    op.create_table(
        "automation_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("automation_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="SUCCESS"),
        sa.Column("trigger", sa.String(100), nullable=False, server_default="USER_TRIGGERED"),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_automation_executions_user_id", "automation_executions", ["user_id"])
    op.create_index("ix_automation_executions_project_id", "automation_executions", ["project_id"])
    op.create_index("ix_automation_executions_automation_type", "automation_executions", ["automation_type"])


def downgrade() -> None:
    op.drop_table("automation_executions")
    op.drop_table("client_requests")
    op.drop_table("project_context_notes")
    op.drop_table("requirement_task_links")
    op.drop_table("analysis_revisions")
    op.drop_table("requirement_risks")
    op.drop_table("requirement_assumptions")
    op.drop_table("clarification_questions")
    op.drop_table("requirements")
    op.drop_table("requirements_analyses")

