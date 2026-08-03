"""Scope Guard for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Separates structural cleanup from meaning changes. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


PROTECTED = (
    "core rule",
    "canonical law",
    "boundary",
    "review bypass",
)

STRUCTURAL = (
    "directory",
    "import",
    "package",
    "readme",
    "index",
    "alias",
    "file group",
)


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str
    next_step: str


def check_scope(change_description: str) -> ScopeDecision:
    lowered = change_description.lower()
    if any(term in lowered for term in PROTECTED):
        return ScopeDecision(False, "meaning boundary mentioned", "write scope note before change")
    if any(term in lowered for term in STRUCTURAL):
        return ScopeDecision(True, "structure-only change", "continue with tests and index update")
    return ScopeDecision(False, "unclear scope", "write scope note before change")
