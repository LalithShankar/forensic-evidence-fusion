"""CSV parser tests."""

from __future__ import annotations

import json

from app.parsers.csv_parser import parse_csv


def test_csv_parser_produces_rows_and_summary() -> None:
    content = b"name,amount\nAlice,10\nBob,20\n"
    result = parse_csv(content, filename="ledger.csv")

    structured = json.loads(result.structured.decode("utf-8"))
    assert structured["row_count"] == 2
    assert structured["columns"] == ["name", "amount"]
    assert structured["rows"][0]["name"] == "Alice"

    readable = result.readable.decode("utf-8")
    assert "ledger.csv" in readable
    assert "Rows: 2" in readable
