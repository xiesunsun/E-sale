"""add payment sagas

Revision ID: d42f7f37957b
Revises: 824474e57906
Create Date: 2026-09-29 14:55:56.640945

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d42f7f37957b"
down_revision: Union[str, Sequence[str], None] = "824474e57906"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "payment_sagas",
        sa.Column(
            "id",
            sa.BigInteger,
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column(
            "order_id",
            sa.BigInteger,
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "idempotency_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("payment_sagas")
