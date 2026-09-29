"""add consumer deliveries

Revision ID: a645790466bd
Revises: 80c7d20e90b6
Create Date: 2026-09-29 15:50:42.633844

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a645790466bd"
down_revision: Union[str, Sequence[str], None] = "80c7d20e90b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "consumer_deliveries",
        sa.Column(
            "event_id",
            sa.BigInteger,
            primary_key=True,
        ),
        sa.Column(
            "event_type",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "aggregate_id",
            sa.BigInteger,
            nullable=False,
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade():
    op.drop_table("consumer_deliveries")
