"""add refunds table

Revision ID: 824474e57906
Revises: 9e40ee93d9a3
Create Date: 2026-09-29 14:38:05.291395

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "824474e57906"
down_revision: Union[str, Sequence[str], None] = "9e40ee93d9a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "refunds",
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
            "status",
            sa.Text(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("refunds")
