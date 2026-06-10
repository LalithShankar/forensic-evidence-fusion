"""Add structured_datasets table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009_structured_datasets"
down_revision: str | None = "008_readable_views"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "structured_datasets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("transformation_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("dataset_type", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
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
        "ix_structured_datasets_artifact_id",
        "structured_datasets",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_structured_datasets_artifact_id",
        table_name="structured_datasets",
    )
    op.drop_table("structured_datasets")
