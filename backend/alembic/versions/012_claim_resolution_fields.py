"""Expand claim_resolutions with deterministic verdict fields."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "012_claim_resolution_fields"
down_revision: str | None = "011_claim_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("claim_resolutions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("result_label", sa.String(length=64), nullable=True),
        )
        batch_op.add_column(
            sa.Column("support_score", sa.Float(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("contradiction_score", sa.Float(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("supporting_event_ids", sa.JSON(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("contradicting_event_ids", sa.JSON(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("unresolved_reason", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("claim_resolutions", schema=None) as batch_op:
        batch_op.drop_column("unresolved_reason")
        batch_op.drop_column("contradicting_event_ids")
        batch_op.drop_column("supporting_event_ids")
        batch_op.drop_column("contradiction_score")
        batch_op.drop_column("support_score")
        batch_op.drop_column("result_label")
