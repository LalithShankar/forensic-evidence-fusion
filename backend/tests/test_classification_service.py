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


def test_csv_classified_by_mime_when_extension_missing() -> None:
    result = classify_artifact(
        original_filename="export",
        file_extension="",
        mime_type="text/csv",
    )
    assert result.artifact_type == "csv"
    assert result.needs_review is False


def test_json_classified_by_extension_when_mime_generic() -> None:
    result = classify_artifact(
        original_filename="events.json",
        file_extension="json",
        mime_type="application/octet-stream",
    )
    assert result.source_family == "Structured"
    assert result.artifact_type == "json"


def test_pdf_classified_with_minimum_confidence() -> None:
    result = classify_artifact(
        original_filename="memo.pdf",
        file_extension="pdf",
        mime_type="application/pdf",
    )
    assert result.artifact_type == "pdf"
    assert result.confidence >= 0.7


def test_whatsapp_zip_export_recognized() -> None:
    result = classify_artifact(
        original_filename="whatsapp_backup.zip",
        file_extension="zip",
        mime_type="application/zip",
    )
    assert result.source_family == "WhatsApp"
    assert result.needs_review is False


def test_empty_filename_falls_back_to_needs_review() -> None:
    result = classify_artifact(
        original_filename="",
        file_extension="",
        mime_type="application/octet-stream",
    )
    assert result.needs_review is True
    assert result.confidence < 0.7
