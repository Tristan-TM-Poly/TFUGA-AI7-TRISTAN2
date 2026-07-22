"""Entropy Mapper for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Maps large draft structures into simple entropy signals. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntropySignal:
    name: str
    severity: str
    suggested_artifact: str


@dataclass(frozen=True)
class EntropyMap:
    scope: str
    signals: tuple[EntropySignal, ...]
    next_safe_action: str


def map_entropy(*, scope: str, changed_files: int = 0, additions: int = 0, connector_residue: int = 0) -> EntropyMap:
    signals: list[EntropySignal] = []
    if changed_files >= 100:
        signals.append(EntropySignal("large_file_count", "high", "architecture_index"))
    if additions >= 5000:
        signals.append(EntropySignal("large_addition_count", "high", "micro_pr_plan"))
    if connector_residue > 0:
        signals.append(EntropySignal("connector_residue", "medium", "alias_registry"))
    if not signals:
        signals.append(EntropySignal("stable_size", "low", "keep_monitoring"))
    return EntropyMap(scope=scope, signals=tuple(signals), next_safe_action="create map before refactor")
