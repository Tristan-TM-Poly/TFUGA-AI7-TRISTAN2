"""Deterministic scoring primitives for Ω-VALUE-OS-T∞."""
from __future__ import annotations

import math
from typing import Iterable, Mapping

from .models import ContextProfile, ValueCase


EXTERNAL_EVIDENCE_FACTORS = {
    0: 0.35,
    1: 0.45,
    2: 0.60,
    3: 0.75,
    4: 0.90,
    5: 1.00,
}


def weighted_geometric_score(case: ValueCase, profile: ContextProfile, *, epsilon: float = 1e-9) -> float:
    """Return a bounded geometric aggregate, explicitly not a probability.

    Missing dimensions receive zero rather than being silently ignored: a profile declares
    what it cares about, and the case must earn those dimensions.
    """
    numerator = 0.0
    denominator = 0.0
    for name, weight in profile.weights.items():
        weight = float(weight)
        if weight <= 0:
            continue
        score = float(case.dimensions.get(name, 0.0))
        numerator += weight * math.log(max(score, epsilon))
        denominator += weight
    if denominator == 0:
        return 0.0
    value = math.exp(numerator / denominator)
    return min(1.0, max(0.0, value))


def debt_penalty(case: ValueCase) -> float:
    """Exponential penalty for crystallization/confidence/technical/risk debt."""
    debt = sum(float(value) for value in case.debts.values())
    return math.exp(-debt)


def closure_factor(case: ValueCase) -> float:
    return 0.25 + 0.75 * case.closure


def reuse_factor(case: ValueCase) -> float:
    return 0.50 + 0.50 * case.reuse


def external_evidence_factor(case: ValueCase) -> float:
    return EXTERNAL_EVIDENCE_FACTORS[int(case.evidence_level)]


def claim_ceiling(case: ValueCase) -> float:
    """Maximum allowed claim strength under R0.1.

    Evidence strength is further reduced by declared uncertainty. This is deliberately
    conservative and heuristic; it is a governance ceiling, not a truth probability.
    """
    return max(0.0, min(1.0, case.evidence_strength * (1.0 - 0.5 * case.uncertainty)))


def effective_value(case: ValueCase, profile: ContextProfile) -> dict[str, float]:
    soft = weighted_geometric_score(case, profile)
    debt = debt_penalty(case)
    external = external_evidence_factor(case)
    closure = closure_factor(case)
    reuse = reuse_factor(case)
    value = soft * debt * external * closure * reuse
    return {
        "soft_score": soft,
        "debt_penalty": debt,
        "external_evidence_factor": external,
        "closure_factor": closure,
        "reuse_factor": reuse,
        "effective_value": min(1.0, max(0.0, value)),
    }


def dominates(left: ValueCase, right: ValueCase, dimensions: Iterable[str]) -> bool:
    """Pareto dominance on declared dimensions. Missing values are zero."""
    dims = tuple(dimensions)
    if not dims:
        return False
    ge_all = all(left.dimensions.get(key, 0.0) >= right.dimensions.get(key, 0.0) for key in dims)
    gt_any = any(left.dimensions.get(key, 0.0) > right.dimensions.get(key, 0.0) for key in dims)
    return ge_all and gt_any


def pareto_frontier(cases: Iterable[ValueCase], dimensions: Iterable[str]) -> tuple[str, ...]:
    cases = tuple(cases)
    dims = tuple(dimensions)
    frontier = []
    for candidate in cases:
        if not any(dominates(other, candidate, dims) for other in cases if other.case_id != candidate.case_id):
            frontier.append(candidate.case_id)
    return tuple(sorted(frontier))


def opportunity_costs(values: Mapping[str, float]) -> dict[str, float]:
    """Gap to the best alternative. This is portfolio opportunity cost, not money."""
    if not values:
        return {}
    ordered = sorted(((float(value), key) for key, value in values.items()), reverse=True)
    best_value, best_id = ordered[0]
    second = ordered[1][0] if len(ordered) > 1 else best_value
    result = {}
    for key, value in values.items():
        numeric = float(value)
        if key == best_id:
            result[key] = max(0.0, best_value - second)
        else:
            result[key] = max(0.0, best_value - numeric)
    return result
