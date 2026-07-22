"""Autonomous Priority Engine for Ω-AIT-CONTINUATION-ENGINE-T.

Ranks safe candidate actions by impact, reversibility, testability, canon gain,
risk, cost, and uncertainty. Planning only; no external execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityCandidate:
    name: str
    impact: int = 0
    reversibility: int = 0
    testability: int = 0
    canon_gain: int = 0
    risk: int = 0
    cost: int = 0
    uncertainty: int = 0

    @property
    def score(self) -> int:
        return self.impact + self.reversibility + self.testability + self.canon_gain - self.risk - self.cost - self.uncertainty


@dataclass(frozen=True)
class PriorityDecision:
    chosen: PriorityCandidate
    ranking: tuple[PriorityCandidate, ...]
    safe_next_action: str


def choose_priority(candidates: tuple[PriorityCandidate, ...]) -> PriorityDecision:
    if not candidates:
        fallback = PriorityCandidate("create_next_action_note", impact=1, reversibility=5, testability=1, canon_gain=1)
        return PriorityDecision(fallback, (fallback,), "Create next-action note.")
    ranking = tuple(sorted(candidates, key=lambda c: c.score, reverse=True))
    chosen = ranking[0]
    return PriorityDecision(chosen, ranking, f"Execute safest artifact plan for: {chosen.name}")
