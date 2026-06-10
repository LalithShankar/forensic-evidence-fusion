"""Heuristic parsing of narrative claim text."""

from __future__ import annotations

import re
from datetime import UTC, datetime

_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?)\b")
_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")


def parse_claim_fields(
    *,
    claim_text: str,
    claimant: str | None,
    claimed_time_text: str | None,
    claimed_people: list[str] | None,
) -> tuple[str | None, datetime | None, list[str], float]:
    """Extract claimed time/people heuristics and compute parse confidence."""
    time_text = claimed_time_text
    normalized_time: datetime | None = None
    people = [person.strip() for person in (claimed_people or []) if person.strip()]

    if not time_text:
        match = _ISO_DATE_RE.search(claim_text)
        if match:
            time_text = match.group(1)

    if time_text:
        try:
            normalized_time = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
            if normalized_time.tzinfo is None:
                normalized_time = normalized_time.replace(tzinfo=UTC)
        except ValueError:
            normalized_time = None

    if not people:
        people = [
            name
            for name in _NAME_RE.findall(claim_text)
            if name.lower() not in {"the", "and", "on", "at"}
        ][:5]

    if claimant and claimant not in people:
        people.insert(0, claimant)

    signals = 0.0
    if time_text:
        signals += 0.35
    if normalized_time:
        signals += 0.2
    if people:
        signals += 0.25
    if claimant:
        signals += 0.1
    if len(claim_text.split()) >= 5:
        signals += 0.1

    parse_confidence = min(0.95, max(0.35, signals))
    return time_text, normalized_time, people, parse_confidence
