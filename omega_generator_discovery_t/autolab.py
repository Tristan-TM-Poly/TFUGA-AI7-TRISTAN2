"""OAK-safe experiment prioritization."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ExperimentCandidate:
    name: str
    expected_residual_reduction: float
    generator_discrimination: float
    information_gain: float
    cost: float
    risk: float
    reversible: bool = True


@dataclass(frozen=True, slots=True)
class ExperimentDecision:
    name: str
    score: float
    approved_for_autonomous_draft: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def prioritize_experiments(
    candidates: Iterable[ExperimentCandidate],
    *,
    risk_limit: float = 0.35,
) -> tuple[ExperimentDecision, ...]:
    decisions = []
    for candidate in candidates:
        if candidate.cost < 0 or candidate.risk < 0:
            raise ValueError("Cost and risk must be non-negative")
        benefit = (
            0.4*candidate.expected_residual_reduction
            + 0.35*candidate.generator_discrimination
            + 0.25*candidate.information_gain
        )
        score = benefit-0.2*candidate.cost-0.5*candidate.risk
        approved = candidate.risk <= risk_limit and candidate.reversible
        if not candidate.reversible:
            reason = "human_approval_required_irreversible"
        elif candidate.risk > risk_limit:
            reason = "human_approval_required_risk"
        else:
            reason = "safe_for_draft_or_simulation_only"
        decisions.append(ExperimentDecision(candidate.name, score, approved, reason))
    return tuple(sorted(decisions, key=lambda item: item.score, reverse=True))
