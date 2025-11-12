"""increase_weight_class_length

Revision ID: b1258634cdcf
Revises: dbbe9058ceac
Create Date: 2025-11-12 19:12:24.268440

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1258634cdcf"
down_revision: Union[str, None] = "dbbe9058ceac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aumentar o tamanho da coluna weight_class de VARCHAR(50) para VARCHAR(100)
    op.alter_column(
        "fights",
        "weight_class",
        type_=sa.String(100),
        existing_type=sa.String(50),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Reverter para VARCHAR(50)
    op.alter_column(
        "fights",
        "weight_class",
        type_=sa.String(50),
        existing_type=sa.String(100),
        existing_nullable=True,
    )
