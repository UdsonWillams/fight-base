"""add_predictions_system

Revision ID: 01b2c20c8206
Revises: 25056ec5942e
Create Date: 2026-02-09 00:32:15.191114

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "01b2c20c8206"
down_revision: Union[str, None] = "25056ec5942e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Finish Methods
    op.create_table(
        "finish_methods",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_pt", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("requires_round", sa.Boolean(), nullable=True),
        sa.Column("requires_scorecard", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 2. User Stats
    op.create_table(
        "user_stats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False),
        sa.Column("total_predictions", sa.Integer(), nullable=False),
        sa.Column("correct_winners", sa.Integer(), nullable=False),
        sa.Column("correct_methods", sa.Integer(), nullable=False),
        sa.Column("correct_rounds", sa.Integer(), nullable=False),
        sa.Column("underdog_bonus_points", sa.Integer(), nullable=False),
        sa.Column("points_this_month", sa.Integer(), nullable=False),
        sa.Column("points_this_year", sa.Integer(), nullable=False),
        sa.Column("global_rank", sa.Integer(), nullable=True),
        sa.Column("monthly_rank", sa.Integer(), nullable=True),
        sa.Column("yearly_rank", sa.Integer(), nullable=True),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("best_streak", sa.Integer(), nullable=False),
        sa.Column("events_participated", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # 3. Predictions
    op.create_table(
        "predictions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("fight_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("predicted_winner_id", sa.UUID(), nullable=True),
        sa.Column("predicted_method_id", sa.UUID(), nullable=True),
        sa.Column("predicted_round", sa.Integer(), nullable=True),
        sa.Column("is_winner_correct", sa.Boolean(), nullable=True),
        sa.Column("is_method_correct", sa.Boolean(), nullable=True),
        sa.Column("is_round_correct", sa.Boolean(), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["fight_id"],
            ["fights.id"],
        ),
        sa.ForeignKeyConstraint(
            ["predicted_method_id"],
            ["finish_methods.id"],
        ),
        sa.ForeignKeyConstraint(
            ["predicted_winner_id"],
            ["fighters.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "fight_id", name="uq_user_fight_prediction"),
    )

    # 4. Event Leaderboards
    op.create_table(
        "event_leaderboards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False),
        sa.Column("correct_winners", sa.Integer(), nullable=False),
        sa.Column("correct_methods", sa.Integer(), nullable=False),
        sa.Column("correct_rounds", sa.Integer(), nullable=False),
        sa.Column("total_predictions", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_user_event_leaderboard"),
    )

    # 5. Leagues
    op.create_table(
        "leagues",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("invite_code", sa.String(length=20), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("max_members", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code"),
    )

    # 6. League Members
    op.create_table(
        "league_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("league_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False),
        sa.Column("rank_in_league", sa.Integer(), nullable=True),
        sa.Column("joined_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["league_id"],
            ["leagues.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("league_id", "user_id", name="uq_league_member"),
    )

    # 7. Achievements
    op.create_table(
        "achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("points_required", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 8. User Achievements
    op.create_table(
        "user_achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=150), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=150), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("achievement_id", sa.UUID(), nullable=False),
        sa.Column("unlocked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    # Seeds - Finish Methods
    import uuid

    finish_methods = [
        ("KO", "Knockout", "Nocaute", "knockout", True, False),
        ("TKO", "Technical Knockout", "Nocaute Técnico", "knockout", True, False),
        ("SUB", "Submission", "Finalização", "submission", True, False),
        ("DEC_U", "Unanimous Decision", "Decisão Unânime", "decision", False, True),
        ("DEC_S", "Split Decision", "Decisão Dividida", "decision", False, True),
        ("DEC_M", "Majority Decision", "Decisão Majoritária", "decision", False, True),
        ("DQ", "Disqualification", "Desqualificação", "other", True, False),
        ("NC", "No Contest", "Sem Resultado", "other", False, False),
        ("DRAW", "Draw", "Empate", "other", False, False),
    ]
    finish_methods_table = sa.table(
        "finish_methods",
        sa.column("id", sa.UUID),
        sa.column("created_by", sa.String),
        sa.column("updated_by", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("name_pt", sa.String),
        sa.column("category", sa.String),
        sa.column("requires_round", sa.Boolean),
        sa.column("requires_scorecard", sa.Boolean),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        finish_methods_table,
        [
            {
                "id": uuid.uuid4(),
                "created_by": "system",
                "updated_by": "system",
                "code": code,
                "name": name,
                "name_pt": name_pt,
                "category": cat,
                "requires_round": req_r,
                "requires_scorecard": req_s,
                "is_active": True,
            }
            for code, name, name_pt, cat, req_r, req_s in finish_methods
        ],
    )

    # Seeds - Achievements
    achievements = [
        (
            "FIRST_PREDICTION",
            "Primeiro Palpite",
            "Faça seu primeiro palpite",
            "📌",
            "milestone",
        ),
        ("PREDICTIONS_10", "Novato", "Complete 10 palpites", "🥉", "milestone"),
        ("PREDICTIONS_50", "Apostador", "Complete 50 palpites", "🥈", "milestone"),
        ("PREDICTIONS_100", "Veterano", "Complete 100 palpites", "🥇", "milestone"),
        ("STREAK_5", "Em Chamas", "5 acertos consecutivos", "🔥", "streak"),
        ("STREAK_10", "Invencível", "10 acertos consecutivos", "⚡", "streak"),
        (
            "UNDERDOG_HUNTER",
            "Caçador de Underdogs",
            "Acerte 5 underdogs",
            "🎯",
            "special",
        ),
        (
            "SUBMISSION_MASTER",
            "Mestre das Subs",
            "Acerte 10 submissões",
            "🥋",
            "accuracy",
        ),
        ("KO_PROPHET", "Profeta do KO", "Acerte 10 KOs", "🥊", "accuracy"),
        (
            "PERFECT_EVENT",
            "Evento Perfeito",
            "Acerte todas as lutas de um evento",
            "🌟",
            "special",
        ),
    ]
    achievements_table = sa.table(
        "achievements",
        sa.column("id", sa.UUID),
        sa.column("created_by", sa.String),
        sa.column("updated_by", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("icon", sa.String),
        sa.column("category", sa.String),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        achievements_table,
        [
            {
                "id": uuid.uuid4(),
                "created_by": "system",
                "updated_by": "system",
                "code": code,
                "name": name,
                "description": desc,
                "icon": icon,
                "category": cat,
                "is_active": True,
            }
            for code, name, desc, icon, cat in achievements
        ],
    )


def downgrade() -> None:
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_table("league_members")
    op.drop_table("leagues")
    op.drop_table("event_leaderboards")
    op.drop_table("predictions")
    op.drop_table("user_stats")
    op.drop_table("finish_methods")
