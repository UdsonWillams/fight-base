"""deprecate_magic_attributes_add_ml_fields

Revision ID: fa3535b5ffa5
Revises: 7fef1d23ba08
Create Date: 2025-11-12 19:51:49.568192

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa3535b5ffa5"
down_revision: Union[str, None] = "7fef1d23ba08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tornar atributos mágicos nullable (deprecados)
    op.alter_column("fighters", "striking", existing_type=sa.Integer(), nullable=True)
    op.alter_column("fighters", "grappling", existing_type=sa.Integer(), nullable=True)
    op.alter_column("fighters", "defense", existing_type=sa.Integer(), nullable=True)
    op.alter_column("fighters", "stamina", existing_type=sa.Integer(), nullable=True)
    op.alter_column("fighters", "speed", existing_type=sa.Integer(), nullable=True)
    op.alter_column("fighters", "strategy", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Reverter para not null
    op.alter_column("fighters", "striking", existing_type=sa.Integer(), nullable=False)
    op.alter_column("fighters", "grappling", existing_type=sa.Integer(), nullable=False)
    op.alter_column("fighters", "defense", existing_type=sa.Integer(), nullable=False)
    op.alter_column("fighters", "stamina", existing_type=sa.Integer(), nullable=False)
    op.alter_column("fighters", "speed", existing_type=sa.Integer(), nullable=False)
    op.alter_column("fighters", "strategy", existing_type=sa.Integer(), nullable=False)
