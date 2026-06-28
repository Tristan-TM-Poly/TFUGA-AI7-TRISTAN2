"""M⁻ negative-memory registry for Ω-INFO²-T.

Every failure mode becomes an anti-error rule. This module provides a small
JSONL-backed registry that can be used locally, in CI, or by future agents.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import InfoObject, OAKReport


@dataclass(slots=True)
class MMinusEntry:
    error_type: str
    cause: str
    detection: str
    prevention_rule: str
    severity: str = "medium"
    source_info_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "MMinusEntry":
        return cls(
            error_type=str(data.get("error_type", "unknown_error")),
            cause=str(data.get("cause", "unknown_cause")),
            detection=str(data.get("detection", "unknown_detection")),
            prevention_rule=str(data.get("prevention_rule", "review before reuse")),
            severity=str(data.get("severity", "medium")),
            source_info_id=data.get("source_info_id") if data.get("source_info_id") is None else str(data.get("source_info_id")),
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            tags=list(data.get("tags", [])) if isinstance(data.get("tags", []), list) else [],
        )


class MMinusRegistry:
    """Append-only negative memory registry."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.entries: list[MMinusEntry] = []
        if self.path and self.path.exists():
            self.load()

    def add(self, entry: MMinusEntry) -> MMinusEntry:
        self.entries.append(entry)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def extend(self, entries: Iterable[MMinusEntry]) -> None:
        for entry in entries:
            self.add(entry)

    def load(self) -> None:
        if not self.path:
            return
        self.entries = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    self.entries.append(MMinusEntry.from_dict(json.loads(line)))

    def find_rules(self, query: str) -> list[str]:
        q = query.lower()
        rules: list[str] = []
        for entry in self.entries:
            haystack = " ".join([entry.error_type, entry.cause, entry.detection, entry.prevention_rule, " ".join(entry.tags)]).lower()
            if q in haystack:
                rules.append(entry.prevention_rule)
        return rules

    def to_list(self) -> list[dict[str, object]]:
        return [entry.to_dict() for entry in self.entries]

    @staticmethod
    def entries_from_oak_report(obj: InfoObject, report: OAKReport) -> list[MMinusEntry]:
        entries: list[MMinusEntry] = []
        for failed in report.checks_failed:
            entries.append(
                MMinusEntry(
                    error_type=f"oak_check_failed:{failed}",
                    cause="; ".join(report.residue) or "OAK check failed without detailed residue.",
                    detection="OAKInfoGate",
                    prevention_rule=_prevention_rule_for_check(failed),
                    severity="high" if failed in {"source_known", "risk_bounded", "truth_not_overclaimed"} else "medium",
                    source_info_id=obj.id,
                    tags=["oak", "info2", failed],
                )
            )
        return entries


def _prevention_rule_for_check(check: str) -> str:
    rules = {
        "source_known": "Do not canonize or publish claims without explicit source/provenance.",
        "date_or_version_known": "Record date/version before using time-sensitive information.",
        "provenance_present": "Record transformation chain before trusting extracted information.",
        "uncertainty_estimated": "Estimate uncertainty tensor before routing to action.",
        "claims_present": "Extract at least one claim/concept/equation before evaluation.",
        "risk_bounded": "Escalate high-risk information to human OAK review.",
        "source_trust_minimum": "Find stronger primary or traceable source before use.",
        "truth_not_overclaimed": "Downgrade to hypothesis and create test before claiming truth.",
        "proof_separated_from_fertility": "Keep truth and fertility as separate scores.",
    }
    return rules.get(check, "Review failed OAK check before reuse.")
