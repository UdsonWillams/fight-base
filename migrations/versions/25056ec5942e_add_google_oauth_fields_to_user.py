"""add_google_oauth_fields_to_user

Revision ID: 25056ec5942e
Revises: 5498edf5c956
Create Date: 2026-01-23 19:29:26.434764

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "25056ec5942e"
down_revision: Union[str, None] = "5498edf5c956"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add provider and google_id columns to users table
    op.add_column(
        "users",
        sa.Column(
            "provider", sa.String(length=50), nullable=False, server_default="local"
        ),
    )
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))

    # Alter password column to be nullable
    op.alter_column(
        "users", "password", existing_type=sa.String(length=255), nullable=True
    )

    # Create index for google_id
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    # Drop index and columns
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_column("users", "google_id")
    op.drop_column("users", "provider")

    # Restore password column to NOT NULL
    # NOTE: This might fail if there are users without passwords (SSO users)
    op.alter_column(
        "users", "password", existing_type=sa.String(length=255), nullable=False
    )
