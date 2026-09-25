"""add job lease fields

Revision ID: 73eddb14a310
Revises: fec8cf4d1356
Create Date: 2026-09-25 21:17:12.733457

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "73eddb14a310"
down_revision: Union[str, Sequence[str], None] = "fec8cf4d1356"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "jobs",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "attempts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "locked_at")
    op.drop_column("jobs", "attempts")
