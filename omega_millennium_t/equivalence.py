"""Bidirectional-equivalence audit.

A frequent source of false progress is proving only one implication while
writing an equivalence symbol.  This module makes both directions explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import OAKLevel


@dataclass(frozen=True)
class DirectionalImplication:
    source: str
    target: str
    justification: str
    oak_level: OAKLevel


@dataclass(frozen=True)
class EquivalenceAudit:
    left: str
    right: str
    forward_present: bool
    reverse_present: bool
    certified_level: OAKLevel
    valid_equivalence: bool
    blockers: tuple[str, ...]


def audit_equivalence(
    left: str,
    right: str,
    implications: Iterable[DirectionalImplication],
    *,
    minimum_level: OAKLevel = OAKLevel.WELL_TYPED,
) -> EquivalenceAudit:
    implications = tuple(implications)
    forward = [item for item in implications if item.source == left and item.target == right]
    reverse = [item for item in implications if item.source == right and item.target == left]
    blockers: list[str] = []
    if not forward:
        blockers.append("missing forward implication")
    if not reverse:
        blockers.append("missing reverse implication")
    forward_level = max((item.oak_level for item in forward), default=OAKLevel.INTUITION)
    reverse_level = max((item.oak_level for item in reverse), default=OAKLevel.INTUITION)
    certified = min(forward_level, reverse_level)
    if forward and forward_level < minimum_level:
        blockers.append("forward implication below required OAK level")
    if reverse and reverse_level < minimum_level:
        blockers.append("reverse implication below required OAK level")
    return EquivalenceAudit(
        left=left,
        right=right,
        forward_present=bool(forward),
        reverse_present=bool(reverse),
        certified_level=certified,
        valid_equivalence=not blockers,
        blockers=tuple(blockers),
    )
