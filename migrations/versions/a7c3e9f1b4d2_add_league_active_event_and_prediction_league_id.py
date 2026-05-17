"""add_league_active_event_and_prediction_league_id

Revision ID: a7c3e9f1b4d2
Revises: b6c8d9e1f2a3
Create Date: 2026-05-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c3e9f1b4d2"
down_revision: Union[str, None] = "b6c8d9e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leagues", sa.Column("active_event_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_leagues_active_event_id",
        "leagues",
        "events",
        ["active_event_id"],
        ["id"],
    )
    op.add_column("predictions", sa.Column("league_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_predictions_league_id",
        "predictions",
        "leagues",
        ["league_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_predictions_league_id", "predictions", type_="foreignkey")
    op.drop_column("predictions", "league_id")
    op.drop_constraint("fk_leagues_active_event_id", "leagues", type_="foreignkey")
    op.drop_column("leagues", "active_event_id")
