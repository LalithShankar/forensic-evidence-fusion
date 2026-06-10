"""Canonical model field presence tests."""

from __future__ import annotations

from app.models.claim import Claim
from app.models.entity import Entity
from app.models.event import EvidenceEvent


def test_evidence_event_has_provenance_and_confidence_fields() -> None:
    columns = {column.name for column in EvidenceEvent.__table__.columns}
    assert "source_confidence" in columns
    assert "provenance_pointer" in columns
    assert "artifact_id" in columns
    assert "original_timestamp_text" in columns


def test_entity_has_confidence_field() -> None:
    columns = {column.name for column in Entity.__table__.columns}
    assert "confidence" in columns
    assert "entity_type" in columns


def test_claim_stub_table_exists() -> None:
    columns = {column.name for column in Claim.__table__.columns}
    assert "claim_text" in columns
    assert "parse_confidence" in columns
