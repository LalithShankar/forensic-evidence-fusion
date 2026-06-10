"""Add readable_views table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008_readable_views"
down_revision: str | None = "007_transformation_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "readable_views",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("transformation_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("view_type", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"]),
        sa.ForeignKeyConstraint(["transformation_id"], ["transformation_records.id"]),
    )
    op.create_index(
        "ix_readable_views_artifact_id",
        "readable_views",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_readable_views_artifact_id", table_name="readable_views")
    op.drop_table("readable_views")
