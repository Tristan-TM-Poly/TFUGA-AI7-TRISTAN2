from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import SuperconductingCandidate
from .oak import OAKAssessment, audit_candidate


@dataclass(frozen=True)
class RankedCandidate:
    candidate: SuperconductingCandidate
    audit: OAKAssessment


@dataclass(frozen=True)
class SearchTrace:
    input_count: int
    structurally_stable_count: int
    electronically_active_count: int
    promoted_count: int


def rank_candidates(candidates: Iterable[SuperconductingCandidate]) -> list[RankedCandidate]:
    ranked = [RankedCandidate(c, audit_candidate(c)) for c in candidates]
    return sorted(
        ranked,
        key=lambda row: (row.audit.status == "PROMOTE", row.audit.score, row.audit.robust_tc_q05_k),
        reverse=True,
    )


def adaptive_filter(candidates: Iterable[SuperconductingCandidate], *, min_oak_score: float = 0.45) -> tuple[list[RankedCandidate], SearchTrace]:
    pool = list(candidates)
    stable = [c for c in pool if c.minimum_stability_margin >= 0.0]
    active = [c for c in stable if c.lambda_total > 0.0 and c.omega_log_k > 0.0]
    audited = rank_candidates(active)
    promoted = [row for row in audited if row.audit.score >= min_oak_score and row.audit.status != "REJECT"]
    trace = SearchTrace(len(pool), len(stable), len(active), len(promoted))
    return promoted, trace


def pareto_front(candidates: Iterable[SuperconductingCandidate]) -> list[SuperconductingCandidate]:
    """Return non-dominated candidates on Tc + practical robustness axes."""
    pool = list(candidates)

    def objectives(c: SuperconductingCandidate) -> tuple[float, ...]:
        a = audit_candidate(c)
        return (a.usable_tc_k, a.robust_tc_q05_k, c.synthesis_score, c.defect_robustness, c.substrate_robustness)

    vectors = {id(c): objectives(c) for c in pool}
    front: list[SuperconductingCandidate] = []
    for candidate in pool:
        v = vectors[id(candidate)]
        dominated = False
        for other in pool:
            if other is candidate:
                continue
            w = vectors[id(other)]
            if all(a >= b for a, b in zip(w, v)) and any(a > b for a, b in zip(w, v)):
                dominated = True
                break
        if not dominated:
            front.append(candidate)
    return front


def compare_counterfactuals(
    reference: SuperconductingCandidate,
    intervention: SuperconductingCandidate,
    *,
    intervention_label: str,
) -> dict[str, float | str]:
    """Compare two independently computed states; no causal physics is fabricated."""
    base = audit_candidate(reference)
    counter = audit_candidate(intervention)
    return {
        "intervention": intervention_label,
        "reference_tc_k": base.usable_tc_k,
        "counterfactual_tc_k": counter.usable_tc_k,
        "delta_tc_k": base.usable_tc_k - counter.usable_tc_k,
        "reference_oak": base.score,
        "counterfactual_oak": counter.score,
    }
