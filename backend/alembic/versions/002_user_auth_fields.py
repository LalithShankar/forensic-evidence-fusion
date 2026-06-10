"""Add auth columns to users table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_user_auth_fields"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
            server_default="analyst",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])


def downgrade() -> None:
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "status")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "display_name")
    op.drop_column("users", "email")
