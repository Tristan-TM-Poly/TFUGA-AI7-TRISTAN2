"""Propulsion score for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Ranks safe task candidates. Planning only; no external execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PropulsionCandidate:
    name: str
    impact: int = 0
    canon_gain: int = 0
    debt_reduction: int = 0
    testability: int = 0
    reversibility: int = 0
    risk: int = 0
    cost: int = 0
    uncertainty: int = 0
    irreversibility: int = 0

    @property
    def score(self) -> int:
        return (
            self.impact
            + self.canon_gain
            + self.debt_reduction
            + self.testability
            + self.reversibility
            - self.risk
            - self.cost
            - self.uncertainty
            - self.irreversibility
        )


def choose_best_propulsion(candidates: tuple[PropulsionCandidate, ...]) -> PropulsionCandidate:
    if not candidates:
        return PropulsionCandidate("next_action_note", impact=1, reversibility=5, testability=1)
    return max(candidates, key=lambda item: item.score)
