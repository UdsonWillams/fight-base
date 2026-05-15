"""add_ctrl_avg_to_fighters

Revision ID: b6c8d9e1f2a3
Revises: a9f5b7c3d2e1
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6c8d9e1f2a3"
down_revision: Union[str, None] = "a9f5b7c3d2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fighters",
        sa.Column("ctrl_avg", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("fighters", "ctrl_avg")
