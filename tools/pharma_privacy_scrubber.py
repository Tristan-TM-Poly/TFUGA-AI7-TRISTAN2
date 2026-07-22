"""Privacy scrubber for pharmacology-safety documentation.

The scrubber is intentionally simple and conservative. It is meant to reduce
accidental leakage of personal health details into public documentation, not to
provide perfect de-identification or legal compliance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)")
DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b")

PERSONAL_CONTEXT_PATTERNS = [
    re.compile(r"\bI took\b", re.IGNORECASE),
    re.compile(r"\bmy dose\b", re.IGNORECASE),
    re.compile(r"\bmy medication\b", re.IGNORECASE),
    re.compile(r"\bI weigh\b", re.IGNORECASE),
    re.compile(r"\bI am\s+\d+\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class ScrubResult:
    text: str
    changed: bool
    warnings: tuple[str, ...]


def scrub_health_details(text: str) -> ScrubResult:
    """Remove obvious identifiers and warn about personal health phrasing."""

    original = text
    warnings: list[str] = []

    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = DATE_RE.sub("[REDACTED_DATE]", text)

    for pattern in PERSONAL_CONTEXT_PATTERNS:
        if pattern.search(original):
            warnings.append(
                "Possible personal health detail detected. Prefer generic safety documentation for public commits."
            )
            break

    return ScrubResult(text=text, changed=(text != original or bool(warnings)), warnings=tuple(warnings))


def assert_public_safe(text: str) -> None:
    """Raise ValueError when obvious personal health detail patterns are found."""

    result = scrub_health_details(text)
    if result.warnings:
        raise ValueError("Potential personal health details detected; scrub before committing publicly.")
