"""Add indexes declared on Sprint 4 models but missing from 005.

Revision ID: 006_sprint4_indexes
Revises: 005_sprint4
"""

from collections.abc import Sequence

from alembic import op

revision: str = "006_sprint4_indexes"
down_revision: str | None = "005_sprint4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = [
    ("ix_automation_executions_status", "automation_executions", ["status"]),
    ("ix_client_requests_request_type", "client_requests", ["request_type"]),
    ("ix_project_context_notes_category", "project_context_notes", ["category"]),
]


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
