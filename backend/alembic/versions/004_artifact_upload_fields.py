"""Expand artifacts table for upload metadata and preservation status."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_artifact_upload_fields"
down_revision: str | None = "003_case_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "original_filename",
                sa.String(length=512),
                nullable=False,
                server_default="",
            ),
        )
        batch_op.add_column(
            sa.Column(
                "file_size_bytes",
                sa.BigInteger(),
                nullable=False,
                server_default="0",
            ),
        )
        batch_op.add_column(
            sa.Column(
                "file_extension",
                sa.String(length=32),
                nullable=False,
                server_default="",
            ),
        )
        batch_op.add_column(
            sa.Column(
                "mime_type",
                sa.String(length=255),
                nullable=False,
                server_default="application/octet-stream",
            ),
        )
        batch_op.add_column(
            sa.Column("uploaded_by", sa.Uuid(as_uuid=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "storage_path",
                sa.String(length=1024),
                nullable=False,
                server_default="",
            ),
        )
        batch_op.add_column(
            sa.Column("content_hash", sa.String(length=64), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=32),
                nullable=False,
                server_default="pending",
            ),
        )
        batch_op.create_foreign_key(
            "fk_artifacts_uploaded_by_users",
            "users",
            ["uploaded_by"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_artifacts_uploaded_by_users", type_="foreignkey")
        batch_op.drop_column("status")
        batch_op.drop_column("content_hash")
        batch_op.drop_column("storage_path")
        batch_op.drop_column("uploaded_at")
        batch_op.drop_column("uploaded_by")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("file_extension")
        batch_op.drop_column("file_size_bytes")
        batch_op.drop_column("original_filename")
