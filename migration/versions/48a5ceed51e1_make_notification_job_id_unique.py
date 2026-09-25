"""make notification job id unique

Revision ID: 48a5ceed51e1
Revises: 4f30e6c09b4e
Create Date: 2026-09-25 22:00:47.148786

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "48a5ceed51e1"
down_revision: Union[str, Sequence[str], None] = "4f30e6c09b4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_notification_deliveries_job_id",
        "notification_deliveries",
        ["job_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_notification_deliveries_job_id",
        "notification_deliveries",
        type_="unique",
    )
