"""Add fighters and fight_simulations tables for FightBase

Revision ID: 2024110100001
Revises: 17cbbf7de12e
Create Date: 2025-11-10 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2024110100001"
down_revision: Union[str, None] = "17cbbf7de12e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar tabela users (renomeando de customers)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by", sa.String(150), nullable=False, default="system"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(150), nullable=False, default="system"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", sa.String(150)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, default="user"),
    )

    # Criar tabela fighters
    op.create_table(
        "fighters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by", sa.String(150), nullable=False, default="system"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(150), nullable=False, default="system"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", sa.String(150)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        # Informações básicas
        sa.Column("name", sa.String(150), nullable=False, index=True),
        sa.Column("nickname", sa.String(100)),
        sa.Column("organization", sa.String(50), nullable=False),
        sa.Column("weight_class", sa.String(50), nullable=False),
        sa.Column("fighting_style", sa.String(100), nullable=False),
        # Atributos de luta (0-100)
        sa.Column("striking", sa.Integer(), nullable=False),
        sa.Column("grappling", sa.Integer(), nullable=False),
        sa.Column("defense", sa.Integer(), nullable=False),
        sa.Column("stamina", sa.Integer(), nullable=False),
        sa.Column("speed", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.Integer(), nullable=False),
        # Estatísticas
        sa.Column("wins", sa.Integer(), default=0),
        sa.Column("losses", sa.Integer(), default=0),
        sa.Column("draws", sa.Integer(), default=0),
        sa.Column("ko_wins", sa.Integer(), default=0),
        sa.Column("submission_wins", sa.Integer(), default=0),
        # Informações adicionais
        sa.Column("age", sa.Integer()),
        sa.Column("height_cm", sa.Float()),
        sa.Column("reach_cm", sa.Float()),
        sa.Column("bio", sa.Text()),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_real", sa.Boolean(), nullable=False, default=True),
        # Relação com criador
        sa.Column(
            "creator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
    )

    # Criar tabela fight_simulations
    op.create_table(
        "fight_simulations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by", sa.String(150), nullable=False, default="system"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(150), nullable=False, default="system"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", sa.String(150)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        # Lutadores envolvidos
        sa.Column(
            "fighter1_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fighters.id"),
            nullable=False,
        ),
        sa.Column(
            "fighter2_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fighters.id"),
            nullable=False,
        ),
        # Resultado
        sa.Column("winner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_type", sa.String(50), nullable=False),
        sa.Column("rounds", sa.Integer(), nullable=False, default=3),
        sa.Column("finish_round", sa.Integer()),
        # Estatísticas
        sa.Column("fighter1_probability", sa.Float(), nullable=False),
        sa.Column("fighter2_probability", sa.Float(), nullable=False),
        # Detalhes
        sa.Column("simulation_details", postgresql.JSON()),
        sa.Column("notes", sa.Text()),
    )

    # Criar índices
    op.create_index("idx_fighters_name", "fighters", ["name"])
    op.create_index("idx_fighters_organization", "fighters", ["organization"])
    op.create_index("idx_fighters_weight_class", "fighters", ["weight_class"])
    op.create_index("idx_fighters_creator", "fighters", ["creator_id"])
    op.create_index("idx_simulations_fighter1", "fight_simulations", ["fighter1_id"])
    op.create_index("idx_simulations_fighter2", "fight_simulations", ["fighter2_id"])
    op.create_index("idx_simulations_winner", "fight_simulations", ["winner_id"])


def downgrade() -> None:
    # Remover índices
    op.drop_index("idx_simulations_winner", "fight_simulations")
    op.drop_index("idx_simulations_fighter2", "fight_simulations")
    op.drop_index("idx_simulations_fighter1", "fight_simulations")
    op.drop_index("idx_fighters_creator", "fighters")
    op.drop_index("idx_fighters_weight_class", "fighters")
    op.drop_index("idx_fighters_organization", "fighters")
    op.drop_index("idx_fighters_name", "fighters")

    # Remover tabelas
    op.drop_table("fight_simulations")
    op.drop_table("fighters")
    op.drop_table("users")
