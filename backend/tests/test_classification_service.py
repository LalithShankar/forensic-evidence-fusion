"""Unit tests for rule-based classification."""

from __future__ import annotations

from app.services.classification_service import classify_artifact


def test_whatsapp_pattern_high_confidence() -> None:
    result = classify_artifact(
        original_filename="WhatsApp Chat with Bob.txt",
        file_extension="txt",
        mime_type="text/plain",
    )
    assert result.source_group == "ThirdParty"
    assert result.source_family == "WhatsApp"
    assert result.confidence >= 0.7
    assert result.needs_review is False


def test_takeout_zip_high_confidence() -> None:
    result = classify_artifact(
        original_filename="takeout-2024.zip",
        file_extension="zip",
        mime_type="application/zip",
    )
    assert result.source_group == "Google"
    assert result.source_family == "Takeout"
    assert result.confidence >= 0.7
    assert result.needs_review is False


def test_unknown_file_low_confidence_needs_review() -> None:
    result = classify_artifact(
        original_filename="random_data.bin",
        file_extension="bin",
        mime_type="application/octet-stream",
    )
    assert result.confidence < 0.7
    assert result.needs_review is True
