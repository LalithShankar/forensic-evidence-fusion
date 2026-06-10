"""Add assistant_logs table for Q&A audit."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "014_assistant_logs"
down_revision: str | None = "013_search_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("limitation_text", sa.Text(), nullable=True),
        sa.Column("insufficient_evidence", sa.Boolean(), nullable=False),
        sa.Column("retrieval_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("source_references", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_assistant_logs_case_id", "assistant_logs", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_assistant_logs_case_id", table_name="assistant_logs")
    op.drop_table("assistant_logs")
