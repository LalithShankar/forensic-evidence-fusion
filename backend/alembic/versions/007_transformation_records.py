"""Add transformation_records table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007_transformation_records"
down_revision: str | None = "006_artifact_classification_and_batch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transformation_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("readable_path", sa.String(length=1024), nullable=True),
        sa.Column("structured_path", sa.String(length=1024), nullable=True),
        sa.Column("failure_notes", sa.Text(), nullable=True),
        sa.Column("limitation_notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_transformation_records_artifact_id",
        "transformation_records",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transformation_records_artifact_id",
        table_name="transformation_records",
    )
    op.drop_table("transformation_records")
