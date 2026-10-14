"""Add agent execution and GitHub integration tables

Revision ID: 004_sprint3
Revises: 003_sprint2
Create Date: 2026-10-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_sprint3"
down_revision: str = "003_sprint2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Agent executions
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_executions_user_id", "agent_executions", ["user_id"])
    op.create_index("ix_agent_executions_status", "agent_executions", ["status"])
    op.create_index("ix_agent_executions_conversation_id", "agent_executions", ["conversation_id"])

    # Agent execution steps
    op.create_table(
        "agent_execution_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("tool_input", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_execution_steps_execution_id", "agent_execution_steps", ["execution_id"])

    # GitHub integrations
    op.create_table(
        "github_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.String(500), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_github_integration_user"),
    )
    op.create_index("ix_github_integrations_user_id", "github_integrations", ["user_id"])


def downgrade() -> None:
    op.drop_table("agent_execution_steps")
    op.drop_table("agent_executions")
    op.drop_table("github_integrations")

