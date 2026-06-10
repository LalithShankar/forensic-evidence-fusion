"""JSON parser producing pretty readable and structured outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ParserOutput:
    """Readable and structured bytes from a parser."""

    readable: bytes
    structured: bytes
    limitation_notes: str | None = None


def parse_json(content: bytes, *, filename: str = "data.json") -> ParserOutput:
    """Parse JSON bytes into normalized structured and readable outputs."""
    text = content.decode("utf-8", errors="replace")
    payload = json.loads(text)
    structured_bytes = json.dumps(
        {"format": "json", "filename": filename, "data": payload},
        indent=2,
    ).encode("utf-8")
    readable_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    return ParserOutput(readable=readable_bytes, structured=structured_bytes)
