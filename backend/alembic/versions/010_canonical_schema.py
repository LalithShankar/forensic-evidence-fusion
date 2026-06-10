"""Add canonical entity, event, claim, and stub tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "010_canonical_schema"
down_revision: str | None = "009_structured_datasets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("source_artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("attributes_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["source_artifact_id"], ["artifacts.id"]),
    )
    op.create_index("ix_entities_case_id", "entities", ["case_id"])

    op.create_table(
        "evidence_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("transformation_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("structured_dataset_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_subtype", sa.String(length=64), nullable=True),
        sa.Column("original_timestamp_text", sa.String(length=256), nullable=True),
        sa.Column("normalized_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("source_confidence", sa.Float(), nullable=False),
        sa.Column("provenance_pointer", sa.String(length=1024), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
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
        sa.ForeignKeyConstraint(["transformation_id"], ["transformation_records.id"]),
        sa.ForeignKeyConstraint(["structured_dataset_id"], ["structured_datasets.id"]),
    )
    op.create_index("ix_evidence_events_case_id", "evidence_events", ["case_id"])
    op.create_index(
        "ix_evidence_events_artifact_id",
        "evidence_events",
        ["artifact_id"],
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=False),
        sa.Column("claim_source_artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("parse_confidence", sa.Float(), nullable=False),
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
        sa.ForeignKeyConstraint(["claim_source_artifact_id"], ["artifacts.id"]),
    )

    op.create_table(
        "claim_resolutions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("claim_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("resolution_status", sa.String(length=32), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
    )

    op.create_table(
        "analyst_notes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("author_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
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
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("analyst_notes")
    op.drop_table("claim_resolutions")
    op.drop_table("claims")
    op.drop_index("ix_evidence_events_artifact_id", table_name="evidence_events")
    op.drop_index("ix_evidence_events_case_id", table_name="evidence_events")
    op.drop_table("evidence_events")
    op.drop_index("ix_entities_case_id", table_name="entities")
    op.drop_table("entities")
