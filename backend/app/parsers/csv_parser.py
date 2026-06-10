"""CSV parser producing readable summary and structured rows."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ParserOutput:
    """Readable and structured bytes from a parser."""

    readable: bytes
    structured: bytes
    limitation_notes: str | None = None


def parse_csv(content: bytes, *, filename: str = "data.csv") -> ParserOutput:
    """Parse CSV bytes into structured rows and a readable summary."""
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no data rows")

    columns = list(rows[0].keys())
    structured_payload = {
        "format": "csv",
        "filename": filename,
        "row_count": len(rows),
        "columns": columns,
        "rows": rows,
    }
    readable_lines = [
        f"CSV summary for {filename}",
        f"Rows: {len(rows)}",
        f"Columns: {', '.join(columns)}",
        "",
        "Preview (first 5 rows):",
    ]
    for index, row in enumerate(rows[:5], start=1):
        readable_lines.append(f"{index}. {json.dumps(row, ensure_ascii=True)}")

    return ParserOutput(
        readable="\n".join(readable_lines).encode("utf-8"),
        structured=json.dumps(structured_payload, indent=2).encode("utf-8"),
    )
