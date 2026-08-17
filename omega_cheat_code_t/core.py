from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

_EPSILON = 1e-12


@dataclass(frozen=True)
class EvolutionState:
    desired_capability: float
    verified_capability: float
    surprise: float = 0.0
    uncertainty: float = 0.0
    opportunity: float = 0.0
    evidence: float = 0.0

    @property
    def residual(self) -> float:
        return max(0.0, self.desired_capability - self.verified_capability)

    def frontier_score(self, *, surprise_weight: float = 1.0) -> float:
        return (
            self.residual
            + surprise_weight * max(0.0, self.surprise)
            + max(0.0, self.uncertainty)
            + max(0.0, self.opportunity)
            - max(0.0, self.evidence)
        )


@dataclass(frozen=True)
class EvolutionCandidate:
    name: str
    success_probability: float
    value: float
    reuse: float
    evidence_gain: float
    option_value: float
    compute_cost: float
    time_cost: float
    risk: float
    debt: float
    novelty_delta: float = 1.0
    internal_closure_coverage: float = 0.0
    verified_marginal_gain: float = 0.0
    capability_retention: float = 1.0
    complexity_reduction: float = 0.0

    def expected_evolution_value(self) -> float:
        probability = min(1.0, max(0.0, self.success_probability))
        numerator = (
            probability
            * max(0.0, self.value)
            * max(0.0, self.reuse)
            * max(0.0, self.evidence_gain)
            * max(0.0, self.option_value)
        )
        denominator = (
            max(0.0, self.compute_cost)
            + max(0.0, self.time_cost)
            + max(0.0, self.risk)
            + max(0.0, self.debt)
        )
        return numerator / max(denominator, _EPSILON)

    def is_redundant(self, *, closure_threshold: float = 0.95) -> bool:
        return self.internal_closure_coverage >= closure_threshold and self.novelty_delta <= 0.0

    def lifecycle_action(self) -> str:
        if self.verified_marginal_gain <= 0.0:
            return "kill"
        if self.capability_retention >= 0.95 and self.complexity_reduction >= 0.25:
            return "distill"
        return "keep"


@dataclass(frozen=True)
class MetaDepthTrial:
    depth: int
    verified_gain: float
    compute_cost: float
    risk: float
    debt: float

    def score(self) -> float:
        denominator = max(0.0, self.compute_cost) + max(0.0, self.risk) + max(0.0, self.debt)
        return max(0.0, self.verified_gain) / max(denominator, _EPSILON)


@dataclass(frozen=True)
class ProofEnvelope:
    claim: str
    evidence: tuple[str, ...]
    counterevidence: tuple[str, ...] = ()
    uncertainty: float = 1.0
    rollback: str = ""

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        if not self.claim.strip():
            errors.append("claim_required")
        if not self.evidence:
            errors.append("evidence_required")
        if not 0.0 <= self.uncertainty <= 1.0:
            errors.append("uncertainty_out_of_range")
        if not self.rollback.strip():
            errors.append("rollback_required")
        return (not errors, tuple(errors))


@dataclass(frozen=True)
class EvolutionPlan:
    plan_id: str
    intent: str
    residual: float
    frontier_score: float
    selected_candidate: str
    selected_eev: float
    selected_meta_depth: int
    lifecycle_action: str
    proof_required: bool
    automatic_merge: bool = False
    remote_mutations: int = 0
    theorem_claimed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def rank_candidates(
    candidates: Iterable[EvolutionCandidate],
    *,
    closure_threshold: float = 0.95,
) -> list[EvolutionCandidate]:
    eligible = [item for item in candidates if not item.is_redundant(closure_threshold=closure_threshold)]
    return sorted(eligible, key=lambda item: (-item.expected_evolution_value(), item.name))


def select_meta_depth(trials: Sequence[MetaDepthTrial]) -> MetaDepthTrial:
    if not trials:
        return MetaDepthTrial(depth=0, verified_gain=0.0, compute_cost=0.0, risk=0.0, debt=0.0)
    return min(trials, key=lambda trial: (-trial.score(), trial.depth))


def compile_evolution_plan(
    intent: str,
    state: EvolutionState,
    candidates: Sequence[EvolutionCandidate],
    meta_trials: Sequence[MetaDepthTrial] = (),
) -> EvolutionPlan:
    if not intent.strip():
        raise ValueError("intent must not be empty")
    ranked = rank_candidates(candidates)
    if not ranked:
        raise ValueError("no eligible evolution candidate")
    selected = ranked[0]
    depth = select_meta_depth(meta_trials)
    payload = {
        "intent": intent.strip(),
        "state": asdict(state),
        "candidate": asdict(selected),
        "meta_depth": asdict(depth),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]
    return EvolutionPlan(
        plan_id=f"cheat-{digest}",
        intent=intent.strip(),
        residual=state.residual,
        frontier_score=state.frontier_score(),
        selected_candidate=selected.name,
        selected_eev=selected.expected_evolution_value(),
        selected_meta_depth=depth.depth,
        lifecycle_action=selected.lifecycle_action(),
        proof_required=True,
    )
