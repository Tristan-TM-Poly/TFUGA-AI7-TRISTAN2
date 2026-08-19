"""Lightweight text leak scanner for public artifacts.

This scanner is deliberately simple. It is not a replacement for professional
secret scanning, but it catches obvious risky tokens before public operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_marker", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("github_token_like", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
)


@dataclass(frozen=True)
class LeakFinding:
    kind: str
    start: int
    end: int

    def to_dict(self) -> dict[str, int | str]:
        return {"kind": self.kind, "start": self.start, "end": self.end}


def scan_text(text: str) -> list[LeakFinding]:
    findings: list[LeakFinding] = []
    for kind, pattern in PATTERNS:
        for match in pattern.finditer(text):
            findings.append(LeakFinding(kind=kind, start=match.start(), end=match.end()))
    return findings


def has_findings(text: str) -> bool:
    return bool(scan_text(text))
