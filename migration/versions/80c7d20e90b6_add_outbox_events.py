"""add outbox events

Revision ID: 80c7d20e90b6
Revises: d42f7f37957b
Create Date: 2026-09-29 15:36:26.374639

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "80c7d20e90b6"
down_revision: Union[str, Sequence[str], None] = "d42f7f37957b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "outbox_events",
        sa.Column(
            "id",
            sa.BigInteger,
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", sa.BigInteger, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "event_type",
            "aggregate_id",
            name="uq_outbox_event_aggregate",
        ),
    )


def downgrade():
    op.drop_table("outbox_events")
