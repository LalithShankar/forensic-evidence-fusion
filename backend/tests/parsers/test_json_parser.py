"""JSON parser tests."""

from __future__ import annotations

import json

from app.parsers.json_parser import parse_json


def test_json_parser_produces_readable_and_structured() -> None:
    content = b'{"event":"login","user":"alice"}'
    result = parse_json(content, filename="events.json")

    structured = json.loads(result.structured.decode("utf-8"))
    assert structured["format"] == "json"
    assert structured["data"]["event"] == "login"

    readable = result.readable.decode("utf-8")
    assert '"event": "login"' in readable
