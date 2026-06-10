"""Rule-based artifact classification from filename, extension, and MIME type."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.artifact import PROVENANCE_UNKNOWN

CONFIDENCE_THRESHOLD = 0.7

_WHATSAPP_PATTERNS = (
    re.compile(r"whatsapp", re.IGNORECASE),
    re.compile(r"wa_chat", re.IGNORECASE),
    re.compile(r"chat.*export", re.IGNORECASE),
)
_TAKEOUT_PATTERNS = (
    re.compile(r"takeout", re.IGNORECASE),
    re.compile(r"google.*takeout", re.IGNORECASE),
)


@dataclass(frozen=True)
class ClassificationResult:
    """Suggested provenance metadata with confidence and review hint."""

    source_group: str
    source_family: str
    artifact_type: str
    confidence: float
    reason: str
    needs_review: bool


def classify_artifact(
    *,
    original_filename: str,
    file_extension: str,
    mime_type: str,
) -> ClassificationResult:
    """Apply filename/MIME/extension rules to suggest artifact category."""
    name_lower = original_filename.lower()
    ext_lower = file_extension.lower()
    mime_lower = mime_type.lower()

    if _matches_any(name_lower, _WHATSAPP_PATTERNS) or (
        ext_lower in {"txt", "zip"} and "whatsapp" in name_lower
    ):
        return ClassificationResult(
            source_group="ThirdParty",
            source_family="WhatsApp",
            artifact_type="chat_export",
            confidence=0.92,
            reason="Filename matches WhatsApp export pattern",
            needs_review=False,
        )

    if ext_lower == "zip" and _matches_any(name_lower, _TAKEOUT_PATTERNS):
        return ClassificationResult(
            source_group="Google",
            source_family="Takeout",
            artifact_type="archive",
            confidence=0.88,
            reason="ZIP filename matches Google Takeout pattern",
            needs_review=False,
        )

    if mime_lower == "text/csv" or ext_lower == "csv":
        return ClassificationResult(
            source_group="Generic",
            source_family="Tabular",
            artifact_type="csv",
            confidence=0.75,
            reason="CSV file extension or MIME type",
            needs_review=False,
        )

    if mime_lower == "application/json" or ext_lower == "json":
        return ClassificationResult(
            source_group="Generic",
            source_family="Structured",
            artifact_type="json",
            confidence=0.75,
            reason="JSON file extension or MIME type",
            needs_review=False,
        )

    if mime_lower == "application/pdf" or ext_lower == "pdf":
        return ClassificationResult(
            source_group="Generic",
            source_family="Document",
            artifact_type="pdf",
            confidence=0.72,
            reason="PDF file extension or MIME type",
            needs_review=False,
        )

    return ClassificationResult(
        source_group=PROVENANCE_UNKNOWN,
        source_family=PROVENANCE_UNKNOWN,
        artifact_type=PROVENANCE_UNKNOWN,
        confidence=0.25,
        reason="No matching classification rule",
        needs_review=True,
    )


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)
