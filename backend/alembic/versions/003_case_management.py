"""Expand cases table and add case_memberships."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003_case_management"
down_revision: str | None = "002_user_auth_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cases", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
        )
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "scenario_type",
                sa.String(length=64),
                nullable=False,
                server_default="general_investigation",
            ),
        )
        batch_op.add_column(sa.Column("date_range_start", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("date_range_end", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column("created_by", sa.Uuid(as_uuid=True), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_cases_created_by_users",
            "users",
            ["created_by"],
            ["id"],
        )

    op.create_table(
        "case_memberships",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("access_level", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_memberships_case_user"),
    )
    op.create_index(
        "ix_case_memberships_user_id",
        "case_memberships",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_case_memberships_user_id", table_name="case_memberships")
    op.drop_table("case_memberships")
    with op.batch_alter_table("cases", schema=None) as batch_op:
        batch_op.drop_constraint("fk_cases_created_by_users", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("date_range_end")
        batch_op.drop_column("date_range_start")
        batch_op.drop_column("scenario_type")
        batch_op.drop_column("description")
        batch_op.drop_column("name")
