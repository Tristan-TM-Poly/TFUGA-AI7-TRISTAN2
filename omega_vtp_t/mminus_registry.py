"""M-minus registry for Ω-VTP-T++.

M^- records failed, unstable, expensive, or misleading lifts/features/operators.
It turns failures into reusable negative memory.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class MMinusEntry:
    key: str
    reason: str
    severity: float
    evidence: str
    suggested_action: str


@dataclass(frozen=True)
class MMinusRegistry:
    entries: Tuple[MMinusEntry, ...]

    def as_dict(self) -> Dict[str, MMinusEntry]:
        return {entry.key: entry for entry in self.entries}

    def add(self, entry: MMinusEntry) -> "MMinusRegistry":
        data = self.as_dict()
        data[entry.key] = entry
        return MMinusRegistry(tuple(data.values()))

    def filter_by_severity(self, minimum: float) -> "MMinusRegistry":
        return MMinusRegistry(tuple(e for e in self.entries if e.severity >= minimum))


def build_mminus_registry(entries: Iterable[MMinusEntry] = ()) -> MMinusRegistry:
    registry = MMinusRegistry(tuple())
    for entry in entries:
        registry = registry.add(entry)
    return registry


def entry_from_oak_status(
    key: str,
    oak_status: str,
    *,
    evidence: str,
    severity: float | None = None,
) -> MMinusEntry | None:
    """Create an M^- entry from an OAK status when it signals risk."""

    status = oak_status.lower()
    risk_words = ("high", "fail", "violation", "m_minus", "unstable", "residual")
    if not any(word in status for word in risk_words):
        return None
    if severity is None:
        severity = 0.9 if "high" in status or "fail" in status else 0.5
    return MMinusEntry(
        key=key,
        reason=oak_status,
        severity=float(severity),
        evidence=evidence,
        suggested_action="increase_degree_or_change_basis_or_reduce_cost",
    )


def merge_registries(*registries: MMinusRegistry) -> MMinusRegistry:
    out = build_mminus_registry()
    for registry in registries:
        for entry in registry.entries:
            existing = out.as_dict().get(entry.key)
            if existing is None or entry.severity >= existing.severity:
                out = out.add(entry)
    return out
