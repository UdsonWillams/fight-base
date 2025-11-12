"""increase_actual_weight_class_length

Revision ID: 7fef1d23ba08
Revises: b1258634cdcf
Create Date: 2025-11-12 19:37:31.994070

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7fef1d23ba08"
down_revision: Union[str, None] = "b1258634cdcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aumentar o tamanho da coluna actual_weight_class de VARCHAR(50) para VARCHAR(100)
    op.alter_column(
        "fighters",
        "actual_weight_class",
        type_=sa.String(100),
        existing_type=sa.String(50),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Reverter para VARCHAR(50)
    op.alter_column(
        "fighters",
        "actual_weight_class",
        type_=sa.String(50),
        existing_type=sa.String(100),
        existing_nullable=True,
    )
