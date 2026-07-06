"""Propulsion score for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Ranks safe task candidates. Planning only; no external execution, deployment,
publication, or merge side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


NEGATIVE_INFINITY = float("-inf")
EPSILON = 1e-9


def _non_negative(value: float | int) -> float:
    """Normalize one score component without letting invalid math drive motion."""
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError("propulsion score components must be finite numbers")
    return max(0.0, numeric)


@dataclass(frozen=True)
class PropulsionCandidate:
    """A reversible planning candidate scored by OAK-safe propulsion pressure.

    Positive terms create useful motion. Negative terms represent entropy, cost,
    and irreversible risk. A blocked candidate is never selected, even if it has
    an attractive impact score.
    """

    name: str
    impact: float = 0
    canon_gain: float = 0
    debt_reduction: float = 0
    testability: float = 0
    reversibility: float = 0
    risk: float = 0
    cost: float = 0
    uncertainty: float = 0
    irreversibility: float = 0
    blocked: bool = False
    review_required: bool = False
    reason: str = ""

    @property
    def positive_mass(self) -> float:
        return sum(
            _non_negative(value)
            for value in (
                self.impact,
                self.canon_gain,
                self.debt_reduction,
                self.testability,
                self.reversibility,
            )
        )

    @property
    def entropy_mass(self) -> float:
        return sum(
            _non_negative(value)
            for value in (
                self.risk,
                self.cost,
                self.uncertainty,
                self.irreversibility,
            )
        )

    @property
    def score(self) -> float:
        if self.blocked:
            return NEGATIVE_INFINITY
        score = self.positive_mass / (1.0 + self.entropy_mass + EPSILON)
        if self.review_required:
            score -= 1.0
        return score

    def explain(self) -> dict[str, float | str | bool]:
        """Return a serializable audit packet for reports and progress memory."""
        return {
            "name": self.name,
            "score": self.score,
            "positive_mass": self.positive_mass,
            "entropy_mass": self.entropy_mass,
            "blocked": self.blocked,
            "review_required": self.review_required,
            "reason": self.reason,
        }


def fallback_candidate() -> PropulsionCandidate:
    """Infinite Useful Work fallback when no explicit candidate is viable."""
    return PropulsionCandidate(
        "next_action_note",
        impact=1,
        canon_gain=1,
        testability=1,
        reversibility=5,
        reason="no viable candidate; create traceable next-action note",
    )


def rank_propulsion(candidates: tuple[PropulsionCandidate, ...]) -> tuple[PropulsionCandidate, ...]:
    """Rank viable candidates from strongest to weakest OAK-safe motion."""
    viable = tuple(candidate for candidate in candidates if candidate.score != NEGATIVE_INFINITY)
    return tuple(sorted(viable, key=lambda item: item.score, reverse=True))


def choose_best_propulsion(candidates: tuple[PropulsionCandidate, ...]) -> PropulsionCandidate:
    ranked = rank_propulsion(candidates)
    if not ranked:
        return fallback_candidate()
    return ranked[0]
