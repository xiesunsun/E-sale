"""add outbox lease fields

Revision ID: ad4fe8be3b13
Revises: a645790466bd
Create Date: 2026-09-29 16:01:45.072226

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ad4fe8be3b13"
down_revision: Union[str, Sequence[str], None] = "a645790466bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "outbox_events",
        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "outbox_events",
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade():
    op.drop_column(
        "outbox_events",
        "attempts",
    )

    op.drop_column(
        "outbox_events",
        "locked_at",
    )
