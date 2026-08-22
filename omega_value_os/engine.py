"""Decision engine for value, automation, and proof-of-better promotion."""
from __future__ import annotations

from math import prod
from typing import Dict, Iterable, Tuple

from .constitution import evaluate_hard_gates, is_sensitive_action
from .models import (
    AutomationCandidate,
    AutomationDecision,
    AutomationLevel,
    AuthorityEnvelope,
    ProofOfBetterReceipt,
)

EPSILON = 1e-9


def _bounded(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def automation_score(candidate: AutomationCandidate) -> float:
    """Compute the Tristan automation score from normalized [0, 1] factors."""
    benefit = prod(
        _bounded(x)
        for x in (
            candidate.repeatability,
            candidate.observability,
            candidate.reversibility,
            candidate.auditability,
            candidate.verified_benefit,
        )
    )
    risk = prod(
        max(EPSILON, _bounded(x))
        for x in (
            candidate.downside,
            candidate.irreversibility,
            candidate.permission_sensitivity,
            candidate.compliance_risk,
            candidate.model_uncertainty,
        )
    )
    return benefit / risk


def decide_automation(
    candidate: AutomationCandidate,
    envelope: AuthorityEnvelope,
    zero_touch_threshold: float = 25.0,
    bounded_threshold: float = 5.0,
) -> AutomationDecision:
    """Promote automation only inside an explicit authority envelope."""
    score = automation_score(candidate)
    gate = evaluate_hard_gates(candidate, envelope)

    if is_sensitive_action(candidate.action):
        return AutomationDecision(
            level=AutomationLevel.HUMAN_APPROVED,
            score=score,
            permitted=False,
            reasons=gate.reasons or ("sensitive action requires approval",),
        )

    if not gate.passed:
        return AutomationDecision(
            level=AutomationLevel.SUGGEST,
            score=score,
            permitted=False,
            reasons=gate.reasons,
        )

    if score >= zero_touch_threshold:
        level = AutomationLevel.ZERO_TOUCH
    elif score >= bounded_threshold:
        level = AutomationLevel.BOUNDED_AUTONOMY
    else:
        level = AutomationLevel.HUMAN_APPROVED

    return AutomationDecision(
        level=level,
        score=score,
        permitted=True,
        reasons=("all hard gates passed",),
    )


def value_objective(
    *,
    verified_value: float,
    trust: float,
    human_benefit: float,
    resilience: float,
    reusability: float,
    optionality: float,
    attention: float,
    cost: float,
    risk: float,
    dependency: float,
    harm: float,
    compliance_debt: float,
) -> float:
    numerator = prod(
        max(0.0, x)
        for x in (
            verified_value,
            trust,
            human_benefit,
            resilience,
            reusability,
            optionality,
        )
    )
    denominator = sum(
        max(0.0, x)
        for x in (
            attention,
            cost,
            risk,
            dependency,
            harm,
            compliance_debt,
        )
    )
    return numerator / max(EPSILON, denominator)


def proof_of_better(
    receipt: ProofOfBetterReceipt,
    required_metrics: Iterable[str] = ("verified_value", "trust", "resilience"),
    max_uncertainty: float = 0.35,
) -> Tuple[bool, Dict[str, float]]:
    """Require hard-gate PASS and non-negative deltas on required metrics.

    This is intentionally conservative. A caller can add richer statistical or
    causal checks, but cannot bypass the hard-gate requirement here.
    """
    deltas = {
        key: receipt.metrics_candidate.get(key, 0.0)
        - receipt.metrics_baseline.get(key, 0.0)
        for key in set(receipt.metrics_candidate) | set(receipt.metrics_baseline)
    }
    if not receipt.hard_gate_passed or receipt.uncertainty > max_uncertainty:
        return False, deltas

    required = tuple(required_metrics)
    if not required:
        return False, deltas

    no_regression = all(deltas.get(metric, float("-inf")) >= 0.0 for metric in required)
    at_least_one_gain = any(deltas.get(metric, 0.0) > 0.0 for metric in required)
    return no_regression and at_least_one_gain, deltas


def meta_stop_rule(verified_gain: float, complexity_debt: float, risk_debt: float) -> bool:
    """Return True when another meta layer should be stopped/pruned."""
    return verified_gain <= (complexity_debt + risk_debt)
