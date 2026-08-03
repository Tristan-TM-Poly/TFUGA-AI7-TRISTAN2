"""Formalization audits that fail closed on placeholders."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from .models import FormalStatus


_PLACEHOLDERS: dict[str, tuple[re.Pattern[str], ...]] = {
    ".lean": (
        re.compile(r"\bsorry\b"),
        re.compile(r"\badmit\b"),
        re.compile(r"\bby\s*\?[_A-Za-z0-9]*"),
    ),
    ".v": (
        re.compile(r"\bAdmitted\b"),
        re.compile(r"\badmit\b"),
    ),
    ".thy": (
        re.compile(r"\bsorry\b"),
        re.compile(r"\boops\b"),
    ),
}


@dataclass(frozen=True)
class FormalAudit:
    path: str
    language: str
    status: FormalStatus
    placeholder_count: int
    placeholder_lines: tuple[int, ...]
    kernel_check_claimed: bool
    independent_rebuild_claimed: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "status": self.status.value,
            "placeholder_count": self.placeholder_count,
            "placeholder_lines": list(self.placeholder_lines),
            "kernel_check_claimed": self.kernel_check_claimed,
            "independent_rebuild_claimed": self.independent_rebuild_claimed,
            "notes": list(self.notes),
        }


def audit_text(
    path: str,
    text: str,
    *,
    kernel_check_claimed: bool = False,
    independent_rebuild_claimed: bool = False,
) -> FormalAudit:
    suffix = Path(path).suffix.lower()
    patterns = _PLACEHOLDERS.get(suffix, ())
    lines: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in patterns):
            lines.append(number)
    if not patterns:
        status = FormalStatus.NOT_FORMALIZED
        language = "unknown"
    elif lines:
        status = FormalStatus.PLACEHOLDERS_PRESENT
        language = {".lean": "Lean", ".v": "Coq", ".thy": "Isabelle"}[suffix]
    elif independent_rebuild_claimed:
        status = FormalStatus.INDEPENDENTLY_REBUILT
        language = {".lean": "Lean", ".v": "Coq", ".thy": "Isabelle"}[suffix]
    elif kernel_check_claimed:
        status = FormalStatus.KERNEL_CHECKED_LOCAL
        language = {".lean": "Lean", ".v": "Coq", ".thy": "Isabelle"}[suffix]
    else:
        status = FormalStatus.DEFINITIONS_ONLY
        language = {".lean": "Lean", ".v": "Coq", ".thy": "Isabelle"}[suffix]
    notes = (
        "absence of a recognized placeholder is not proof of semantic completeness",
        "kernel check and independent rebuild require external evidence receipts",
    )
    return FormalAudit(
        path=path,
        language=language,
        status=status,
        placeholder_count=len(lines),
        placeholder_lines=tuple(lines),
        kernel_check_claimed=kernel_check_claimed,
        independent_rebuild_claimed=independent_rebuild_claimed,
        notes=notes,
    )


def audit_paths(paths: Iterable[str | Path]) -> tuple[FormalAudit, ...]:
    reports: list[FormalAudit] = []
    for raw in sorted(Path(path) for path in paths):
        reports.append(audit_text(str(raw), raw.read_text(encoding="utf-8")))
    return tuple(reports)


def promotion_allowed(report: FormalAudit) -> bool:
    return (
        report.placeholder_count == 0
        and report.status in {
            FormalStatus.KERNEL_CHECKED_LOCAL,
            FormalStatus.INDEPENDENTLY_REBUILT,
        }
    )
