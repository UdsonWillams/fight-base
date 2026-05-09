"""add_performance_indexes

Revision ID: c1d3e5f7a9b2
Revises: 01b2c20c8206
Create Date: 2026-05-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c1d3e5f7a9b2"
down_revision: Union[str, None] = "01b2c20c8206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fighters
    op.create_index("ix_fighters_name", "fighters", ["name"])
    op.create_index(
        "ix_fighters_actual_weight_class", "fighters", ["actual_weight_class"]
    )
    op.create_index(
        "ix_fighters_org_weight",
        "fighters",
        ["last_organization_fight", "actual_weight_class"],
    )

    # Fight simulations
    op.create_index(
        "ix_fight_simulations_fighter1", "fight_simulations", ["fighter1_id"]
    )
    op.create_index(
        "ix_fight_simulations_fighter2", "fight_simulations", ["fighter2_id"]
    )
    op.create_index(
        "ix_fight_simulations_created_at", "fight_simulations", ["created_at"]
    )

    # Predictions
    op.create_index(
        "ix_predictions_user_processed", "predictions", ["user_id", "processed_at"]
    )
    op.create_index("ix_predictions_fight_id", "predictions", ["fight_id"])

    # Event leaderboards
    op.create_index(
        "ix_event_leaderboards_event_points",
        "event_leaderboards",
        ["event_id", "total_points"],
    )


def downgrade() -> None:
    op.drop_index("ix_event_leaderboards_event_points", table_name="event_leaderboards")
    op.drop_index("ix_predictions_fight_id", table_name="predictions")
    op.drop_index("ix_predictions_user_processed", table_name="predictions")
    op.drop_index("ix_fight_simulations_created_at", table_name="fight_simulations")
    op.drop_index("ix_fight_simulations_fighter2", table_name="fight_simulations")
    op.drop_index("ix_fight_simulations_fighter1", table_name="fight_simulations")
    op.drop_index("ix_fighters_org_weight", table_name="fighters")
    op.drop_index("ix_fighters_actual_weight_class", table_name="fighters")
    op.drop_index("ix_fighters_name", table_name="fighters")
