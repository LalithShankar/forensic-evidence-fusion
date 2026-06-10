"""Add provenance metadata columns to artifacts."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_artifact_provenance_metadata"
down_revision: str | None = "004_artifact_upload_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNKNOWN_DEFAULT = "unknown"


def upgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_group",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "source_family",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "artifact_type",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "collection_method",
                sa.String(length=128),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "parser_class",
                sa.String(length=64),
                nullable=False,
                server_default=_UNKNOWN_DEFAULT,
            ),
        )
        batch_op.add_column(
            sa.Column("provenance_notes", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("artifacts", schema=None) as batch_op:
        batch_op.drop_column("provenance_notes")
        batch_op.drop_column("parser_class")
        batch_op.drop_column("collection_method")
        batch_op.drop_column("artifact_type")
        batch_op.drop_column("source_family")
        batch_op.drop_column("source_group")
