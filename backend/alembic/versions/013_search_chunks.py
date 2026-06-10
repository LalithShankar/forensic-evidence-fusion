"""Add search_chunks table for RAG indexing."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "013_search_chunks"
down_revision: str | None = "012_claim_resolution_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "search_chunks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("readable_view_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_group", sa.String(length=128), nullable=False),
        sa.Column("provenance_pointer", sa.String(length=1024), nullable=True),
        sa.Column("filter_metadata", sa.JSON(), nullable=True),
        sa.Column("index_status", sa.String(length=32), nullable=False),
        sa.Column("index_error", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"]),
        sa.ForeignKeyConstraint(["readable_view_id"], ["readable_views.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["evidence_events.id"]),
    )
    op.create_index("ix_search_chunks_case_id", "search_chunks", ["case_id"])
    op.create_index(
        "ix_search_chunks_artifact_id",
        "search_chunks",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_search_chunks_artifact_id", table_name="search_chunks")
    op.drop_index("ix_search_chunks_case_id", table_name="search_chunks")
    op.drop_table("search_chunks")
