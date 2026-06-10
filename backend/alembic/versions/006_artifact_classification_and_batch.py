"""Add batch grouping and classification fields to artifacts."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006_artifact_classification_and_batch"
down_revision: str | None = "005_artifact_provenance_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNKNOWN_DEFAULT = "unknown"


def upgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("upload_batch_id", sa.Uuid(as_uuid=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column("classification_confidence", sa.Float(), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "suggested_source_group",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "suggested_source_family",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "suggested_artifact_type",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column("classification_reason", sa.Text(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("blocker_notes", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.drop_column("blocker_notes")
        batch_op.drop_column("classification_reason")
        batch_op.drop_column("suggested_artifact_type")
        batch_op.drop_column("suggested_source_family")
        batch_op.drop_column("suggested_source_group")
        batch_op.drop_column("classification_confidence")
        batch_op.drop_column("upload_batch_id")
