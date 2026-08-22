"""Evidence-aware optimization ROI ranking for Omega Compute Physics R0.6.

The score combines estimated savings, usage, static change impact and engineering
effort while discounting stale/weak evidence through confidence debt. It is a
prioritization proxy, not realized financial ROI or a guarantee that an
optimization exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OptimizationOpportunity:
    repository: str
    node: str
    impact_score: float
    estimated_relative_savings: float
    usage_weight: float
    engineering_effort_hours: float
    confidence_debt: float
    regression_weight: float = 1.0
    evidence_note: str = ""


@dataclass(frozen=True)
class OptimizationROIRow:
    repository: str
    node: str
    gross_value_proxy: float
    evidence_discount: float
    effort_hours: float
    roi_proxy: float
    remeasure_first: bool
    priority: str
    status: str = "optimization-roi-proxy"
    oak_warning: str = (
        "ROI is a dimensionless prioritization proxy based on supplied estimates. "
        "It is not realized money, guaranteed savings or proof that an optimization is feasible."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_opportunity(
    opportunity: OptimizationOpportunity,
    *,
    remeasure_debt_threshold: float = 0.55,
) -> OptimizationROIRow:
    if opportunity.impact_score < 0:
        raise ValueError("impact_score must be non-negative")
    if not 0.0 <= opportunity.estimated_relative_savings <= 1.0:
        raise ValueError("estimated_relative_savings must be in [0, 1]")
    if opportunity.usage_weight < 0:
        raise ValueError("usage_weight must be non-negative")
    if opportunity.engineering_effort_hours <= 0:
        raise ValueError("engineering_effort_hours must be positive")
    if not 0.0 <= opportunity.confidence_debt <= 1.0:
        raise ValueError("confidence_debt must be in [0, 1]")
    if opportunity.regression_weight < 0:
        raise ValueError("regression_weight must be non-negative")

    gross = (
        opportunity.impact_score
        * opportunity.estimated_relative_savings
        * opportunity.usage_weight
        * opportunity.regression_weight
    )
    evidence_discount = max(0.05, 1.0 - opportunity.confidence_debt)
    roi = gross * evidence_discount / opportunity.engineering_effort_hours
    remeasure_first = opportunity.confidence_debt >= remeasure_debt_threshold
    if remeasure_first:
        priority = "remeasure-before-optimization"
    elif roi >= 1.0:
        priority = "highest-optimization-priority"
    elif roi >= 0.25:
        priority = "high-optimization-priority"
    elif roi > 0.0:
        priority = "candidate"
    else:
        priority = "defer"
    return OptimizationROIRow(
        repository=opportunity.repository,
        node=opportunity.node,
        gross_value_proxy=gross,
        evidence_discount=evidence_discount,
        effort_hours=opportunity.engineering_effort_hours,
        roi_proxy=roi,
        remeasure_first=remeasure_first,
        priority=priority,
    )


def rank_optimization_roi(
    opportunities: Sequence[OptimizationOpportunity],
) -> tuple[OptimizationROIRow, ...]:
    rows = [score_opportunity(row) for row in opportunities]
    return tuple(sorted(
        rows,
        key=lambda row: (
            row.remeasure_first,
            -row.roi_proxy,
            row.repository,
            row.node,
        ),
    ))
