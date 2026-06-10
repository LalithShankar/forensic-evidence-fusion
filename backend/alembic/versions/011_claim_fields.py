"""Expand claims table with narrative entry fields."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "011_claim_fields"
down_revision: str | None = "010_canonical_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("claimant", sa.String(length=256), nullable=True),
        )
        batch_op.add_column(
            sa.Column("claimed_time_text", sa.String(length=256), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "claimed_time_normalized",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        batch_op.add_column(sa.Column("claimed_people", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("claim_source", sa.String(length=64), nullable=True),
        )
        batch_op.add_column(
            sa.Column("created_by", sa.Uuid(as_uuid=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=32),
                nullable=False,
                server_default="active",
            ),
        )
        batch_op.create_foreign_key(
            "fk_claims_created_by_users",
            "users",
            ["created_by"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.drop_constraint("fk_claims_created_by_users", type_="foreignkey")
        batch_op.drop_column("status")
        batch_op.drop_column("created_by")
        batch_op.drop_column("claim_source")
        batch_op.drop_column("claimed_people")
        batch_op.drop_column("claimed_time_normalized")
        batch_op.drop_column("claimed_time_text")
        batch_op.drop_column("claimant")
