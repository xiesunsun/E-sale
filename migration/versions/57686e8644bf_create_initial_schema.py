"""create initial schema

Revision ID: 57686e8644bf
Revises:
Create Date: 2026-09-24 14:33:54.509311

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "57686e8644bf"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.BigInteger, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("order_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("status", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("payments")
    op.drop_table("orders")
