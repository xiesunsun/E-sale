"""add idempotency keys

Revision ID: b67328bb375c
Revises: aa027196a9c4
Create Date: 2026-09-24 15:55:03.185201

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b67328bb375c"
down_revision: Union[str, Sequence[str], None] = "aa027196a9c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "idempotency_keys",
        sa.Column("idempotency_key", sa.Text(), primary_key=True),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("response_data", postgresql.JSONB(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("idempotency_keys")
