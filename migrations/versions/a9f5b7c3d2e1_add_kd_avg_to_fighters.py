"""add_kd_avg_to_fighters

Revision ID: a9f5b7c3d2e1
Revises: d8e4f6a2c7b3
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9f5b7c3d2e1"
down_revision: Union[str, None] = "d8e4f6a2c7b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fighters",
        sa.Column("kd_avg", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("fighters", "kd_avg")
