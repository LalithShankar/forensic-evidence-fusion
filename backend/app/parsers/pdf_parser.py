"""PDF text extraction parser (MVP — literal string extraction)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParserOutput:
    """Readable and structured bytes from a parser."""

    readable: bytes
    structured: bytes
    limitation_notes: str | None = None


_PDF_LITERAL_RE = re.compile(r"\(([^)\\]*(?:\\.[^)\\]*)*)\)")


def parse_pdf(content: bytes, *, filename: str = "document.pdf") -> ParserOutput:
    """Extract text literals from a PDF for readable preview and structured metadata."""
    decoded = content.decode("latin-1", errors="ignore")
    literals = _PDF_LITERAL_RE.findall(decoded)
    cleaned = [_unescape_pdf_literal(item) for item in literals]
    text = " ".join(part.strip() for part in cleaned if part.strip())

    if not text:
        raise ValueError("No extractable text found in PDF")

    preview = text[:2000]
    limitation = None
    if len(text) > len(preview):
        limitation = "Text preview truncated to 2000 characters."

    structured_payload = {
        "format": "pdf",
        "filename": filename,
        "text_length": len(text),
        "text_preview": preview,
    }
    readable_lines = [
        f"PDF text preview for {filename}",
        f"Extracted length: {len(text)} characters",
        "",
        preview,
    ]
    return ParserOutput(
        readable="\n".join(readable_lines).encode("utf-8"),
        structured=json.dumps(structured_payload, indent=2).encode("utf-8"),
        limitation_notes=limitation,
    )


def _unescape_pdf_literal(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .replace(r"\n", "\n")
    )
