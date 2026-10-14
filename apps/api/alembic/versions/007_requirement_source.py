"""Record whether a requirement was stated by the client or suggested by the AI.

Revision ID: 007_requirement_source
Revises: 006_sprint4_indexes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_requirement_source"
down_revision: str | None = "006_sprint4_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("requirements", sa.Column("source", sa.String(30), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("requirements") as batch:
        batch.drop_column("source")
