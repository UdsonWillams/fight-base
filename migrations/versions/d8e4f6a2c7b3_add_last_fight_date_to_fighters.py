"""add_last_fight_date_to_fighters

Revision ID: d8e4f6a2c7b3
Revises: c1d3e5f7a9b2
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8e4f6a2c7b3"
down_revision: Union[str, None] = "c1d3e5f7a9b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fighters",
        sa.Column(
            "last_fight_date",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("fighters", "last_fight_date")
