"""PDF parser tests."""

from __future__ import annotations

import json

from app.parsers.pdf_parser import parse_pdf


def test_pdf_parser_extracts_literal_text() -> None:
    content = b"%PDF-1.4 BT (Hello PDF evidence) Tj ET"
    result = parse_pdf(content, filename="memo.pdf")

    structured = json.loads(result.structured.decode("utf-8"))
    assert "Hello PDF evidence" in structured["text_preview"]

    readable = result.readable.decode("utf-8")
    assert "Hello PDF evidence" in readable


def test_pdf_parser_raises_when_no_text() -> None:
    try:
        parse_pdf(b"%PDF-1.4 empty object stream", filename="blank.pdf")
    except ValueError as exc:
        assert "extractable text" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for empty PDF text")
