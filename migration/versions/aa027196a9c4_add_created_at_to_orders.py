"""add created_at to orders

Revision ID: aa027196a9c4
Revises: 57686e8644bf
Create Date: 2026-09-24 14:39:41.694813

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "aa027196a9c4"
down_revision: Union[str, Sequence[str], None] = "57686e8644bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "created_at")
