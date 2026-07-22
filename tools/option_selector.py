"""Option Selector for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Compares candidate options by usefulness, canon gain, testability, reversibility,
cost, and uncertainty. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateOption:
    name: str
    usefulness: int = 0
    canon_gain: int = 0
    testability: int = 0
    reversibility: int = 0
    cost: int = 0
    uncertainty: int = 0

    @property
    def score(self) -> int:
        return self.usefulness + self.canon_gain + self.testability + self.reversibility - self.cost - self.uncertainty


def choose_option(options: tuple[CandidateOption, ...]) -> CandidateOption:
    if not options:
        return CandidateOption("next_action_note", usefulness=1, reversibility=5)
    return max(options, key=lambda option: option.score)
