"""add job retry schedule

Revision ID: 9e40ee93d9a3
Revises: 48a5ceed51e1
Create Date: 2026-09-25 22:19:43.748203

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9e40ee93d9a3"
down_revision: Union[str, Sequence[str], None] = "48a5ceed51e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "jobs",
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "next_attempt_at")
