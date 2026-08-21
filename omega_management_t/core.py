from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ManagementSignal:
    name: str
    observed: float
    outcome_relevance: float
    confidence: float = 1.0
    source: str = "unspecified"

    def __post_init__(self) -> None:
        for value in (self.observed, self.outcome_relevance, self.confidence):
            if not isfinite(value):
                raise ValueError("management signals must be finite")
        if not 0.0 <= self.outcome_relevance <= 1.0:
            raise ValueError("outcome_relevance must be in [0, 1]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ManagementState:
    verified_outcome: float
    autonomy: float
    resilience: float
    decision_quality: float
    capability_growth: float
    friction: float
    leader_dependency: float
    burnout_risk: float
    management_cost: float

    def __post_init__(self) -> None:
        values = tuple(self.__dict__.values())
        if not all(isfinite(v) for v in values):
            raise ValueError("management state values must be finite")
        if any(v < 0 for v in values):
            raise ValueError("management state values must be non-negative")


@dataclass(frozen=True)
class InterventionCandidate:
    candidate_id: str
    expected_verified_gain: float
    cost: float
    risk: float
    friction: float
    reversibility: float
    evidence_confidence: float
    authorized: bool = False
    hard_blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        numeric = (
            self.expected_verified_gain,
            self.cost,
            self.risk,
            self.friction,
            self.reversibility,
            self.evidence_confidence,
        )
        if not all(isfinite(v) for v in numeric):
            raise ValueError("candidate metrics must be finite")
        if self.cost < 0 or self.risk < 0 or self.friction < 0:
            raise ValueError("cost/risk/friction must be non-negative")
        if not 0 <= self.reversibility <= 1 or not 0 <= self.evidence_confidence <= 1:
            raise ValueError("reversibility/confidence must be in [0, 1]")


@dataclass(frozen=True)
class ManagementReceipt:
    baseline: Mapping[str, float]
    intervention_id: str
    observed_result: Mapping[str, float]
    uncertainty: float
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    authority_checked: bool = False
    rollback_available: bool = False


def leadership_value(state: ManagementState) -> float:
    """Evidence-oriented leadership index, not a personnel rating.

    Uses an additive numerator to avoid accidental zeroing of the whole index and a
    +1 denominator guard. The metric is intentionally local and context-dependent.
    """
    numerator = (
        state.verified_outcome
        + state.autonomy
        + state.resilience
        + state.decision_quality
        + state.capability_growth
    )
    denominator = 1.0 + state.friction + state.leader_dependency + state.burnout_risk + state.management_cost
    value = numerator / denominator
    if not isfinite(value):
        raise ValueError("derived leadership value must be finite")
    return value


def absence_resilience(performance_without_leader: float, normal_performance: float) -> float:
    if not isfinite(performance_without_leader) or not isfinite(normal_performance):
        raise ValueError("performance must be finite")
    if normal_performance <= 0:
        raise ValueError("normal_performance must be > 0")
    return performance_without_leader / normal_performance


def proxy_gap(proxy: ManagementSignal, direct_outcome: ManagementSignal) -> float:
    """Return how weakly a proxy is justified relative to a direct outcome signal.

    0 means equally outcome-relevant/confident; larger values mean the proxy should
    receive less decision weight. This does not infer causality or discrimination.
    """
    proxy_weight = proxy.outcome_relevance * proxy.confidence
    outcome_weight = direct_outcome.outcome_relevance * direct_outcome.confidence
    return max(0.0, outcome_weight - proxy_weight)


def _priority(c: InterventionCandidate) -> float:
    if c.hard_blockers or not c.authorized:
        return float("-inf")
    burden = 1.0 + c.cost + c.risk + c.friction
    score = (c.expected_verified_gain * c.evidence_confidence * (0.5 + 0.5 * c.reversibility)) / burden
    return score if isfinite(score) else float("-inf")


def prioritize_interventions(candidates: Iterable[InterventionCandidate]) -> list[InterventionCandidate]:
    """Rank only authorized, unblocked candidates; preserve ties deterministically.

    Ranking is recommendation-only. `authorized=True` is caller-supplied metadata,
    not proof of real-world authority.
    """
    eligible = [c for c in candidates if c.authorized and not c.hard_blockers]
    return sorted(eligible, key=lambda c: (-_priority(c), c.candidate_id))
