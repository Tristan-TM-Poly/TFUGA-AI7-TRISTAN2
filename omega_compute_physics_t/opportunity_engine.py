"""Optimization opportunity discovery for Omega Compute Physics R0.7.

This module separates "worth measuring" from "worth optimizing". Scores are
transparent prioritization heuristics, not measured speedups, causal claims or
financial returns.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OpportunityEvidence:
    repository: str
    node: str
    static_complexity: float
    graph_centrality: float
    usage_weight: float
    regression_signal: float
    expected_savings_prior: float
    confidence_debt: float
    engineering_effort_hours: float
    benchmark_cost: float = 1.0
    evidence_note: str = ""


@dataclass(frozen=True)
class OpportunityDecision:
    repository: str
    node: str
    measurement_priority: float
    optimization_priority: float
    action: str
    evidence_discount: float
    status: str = "optimization-opportunity-candidate"
    oak_warning: str = (
        "Opportunity scores prioritize measurement and optimization work. They "
        "do not prove a bottleneck, feasible optimization, causal mechanism, "
        "speedup, or realized economic value."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_optimization_opportunity(
    evidence: OpportunityEvidence,
    *,
    remeasure_debt_threshold: float = 0.55,
) -> OpportunityDecision:
    nonnegative = {
        "static_complexity": evidence.static_complexity,
        "graph_centrality": evidence.graph_centrality,
        "usage_weight": evidence.usage_weight,
        "regression_signal": evidence.regression_signal,
        "engineering_effort_hours": evidence.engineering_effort_hours,
        "benchmark_cost": evidence.benchmark_cost,
    }
    for name, value in nonnegative.items():
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    if evidence.engineering_effort_hours <= 0:
        raise ValueError("engineering_effort_hours must be positive")
    if evidence.benchmark_cost <= 0:
        raise ValueError("benchmark_cost must be positive")
    if not 0.0 <= evidence.expected_savings_prior <= 1.0:
        raise ValueError("expected_savings_prior must be in [0, 1]")
    if not 0.0 <= evidence.confidence_debt <= 1.0:
        raise ValueError("confidence_debt must be in [0, 1]")

    structural = 1.0 + evidence.static_complexity
    central = 1.0 + evidence.graph_centrality
    regression = 1.0 + evidence.regression_signal
    measurement_priority = (
        structural
        * central
        * regression
        * (0.25 + evidence.confidence_debt)
        / evidence.benchmark_cost
    )
    evidence_discount = max(0.05, 1.0 - evidence.confidence_debt)
    optimization_priority = (
        structural
        * central
        * max(0.0, evidence.usage_weight)
        * evidence.expected_savings_prior
        * regression
        * evidence_discount
        / evidence.engineering_effort_hours
    )

    if evidence.confidence_debt >= remeasure_debt_threshold:
        action = "remeasure-first"
    elif evidence.regression_signal > 0 and optimization_priority >= 1.0:
        action = "optimize-regression"
    elif optimization_priority >= 1.0:
        action = "optimize-candidate"
    elif measurement_priority >= 1.0:
        action = "benchmark-candidate"
    else:
        action = "defer"

    return OpportunityDecision(
        repository=evidence.repository,
        node=evidence.node,
        measurement_priority=measurement_priority,
        optimization_priority=optimization_priority,
        action=action,
        evidence_discount=evidence_discount,
    )


def rank_optimization_opportunities(
    rows: Sequence[OpportunityEvidence],
) -> tuple[OpportunityDecision, ...]:
    decisions = [score_optimization_opportunity(row) for row in rows]
    action_rank = {
        "optimize-regression": 0,
        "optimize-candidate": 1,
        "remeasure-first": 2,
        "benchmark-candidate": 3,
        "defer": 4,
    }
    return tuple(
        sorted(
            decisions,
            key=lambda row: (
                action_rank[row.action],
                -row.optimization_priority,
                -row.measurement_priority,
                row.repository,
                row.node,
            ),
        )
    )
