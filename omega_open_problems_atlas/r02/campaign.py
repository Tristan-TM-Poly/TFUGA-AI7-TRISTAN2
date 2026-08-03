"""Finite adaptive campaign allocation with no permanent total cap."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
from math import isfinite
from typing import Iterable

from .models import CampaignAllocation, ProblemLead, ProofObligation


@dataclass(frozen=True)
class ProblemScore:
    problem_id: str
    impact: float
    transferability: float
    testability: float
    formalizability: float
    source_confidence: float
    difficulty: float
    uncertainty: float
    maintenance_cost: float

    def value(self) -> float:
        numerator = (
            max(0.0, self.impact)
            * max(0.0, self.transferability)
            * max(0.0, self.testability)
            * max(0.0, self.formalizability)
            * max(0.0, self.source_confidence)
        )
        denominator = max(
            1e-9,
            max(0.0, self.difficulty)
            * max(0.0, self.uncertainty)
            * max(0.0, self.maintenance_cost),
        )
        result = numerator / denominator
        return round(result, 12) if isfinite(result) else 0.0


def default_score(lead: ProblemLead) -> ProblemScore:
    status_weight = {
        "DISCOVERED": 0.15,
        "SOURCE_REPORTED": 0.35,
        "LICENSE_REVIEW_REQUIRED": 0.20,
        "STATUS_RECHECK_REQUIRED": 0.25,
        "NORMALIZED": 0.45,
        "LITERATURE_BASELINED": 0.70,
        "INDEPENDENTLY_CHECKED_OPEN": 1.00,
        "PARTIALLY_RESOLVED": 0.75,
        "RESOLVED": 0.50,
        "DISPUTED": 0.10,
        "REJECTED": 0.01,
    }[lead.lead_status.value]
    domain_span = min(1.0, 0.25 + 0.08 * len(set(lead.domains)))
    method_span = min(1.0, 0.30 + 0.07 * len(set(lead.methods)))
    source_confidence = status_weight
    uncertainty = max(0.10, 1.10 - status_weight)
    return ProblemScore(
        problem_id=lead.lead_id,
        impact=float(lead.metadata.get("impact", 0.55)),
        transferability=float(lead.metadata.get("transferability", domain_span)),
        testability=float(lead.metadata.get("testability", method_span)),
        formalizability=float(lead.metadata.get("formalizability", 0.50)),
        source_confidence=source_confidence,
        difficulty=float(lead.metadata.get("difficulty", 0.75)),
        uncertainty=uncertainty,
        maintenance_cost=float(lead.metadata.get("maintenance_cost", 0.50)),
    )


def allocate_campaign(
    leads: Iterable[ProblemLead],
    obligations: Iterable[ProofObligation],
    total_budget: int,
) -> tuple[CampaignAllocation, ...]:
    """Allocate exactly a finite requested budget.

    ``total_budget`` is an invocation budget, not a permanent architectural cap.
    Allocation is weighted round-robin across score-ranked obligations so a
    single prestigious problem cannot starve the rest of the portfolio.
    """
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    lead_map = {lead.lead_id: lead for lead in leads}
    scored: list[tuple[float, ProofObligation]] = []
    for obligation in obligations:
        lead = lead_map.get(obligation.problem_id)
        if lead is None:
            continue
        value = default_score(lead).value()
        scored.append((value, obligation))
    if total_budget and not scored:
        raise ValueError("no eligible obligations")
    scored.sort(key=lambda pair: (-pair[0], pair[1].obligation_id))

    allocations: list[CampaignAllocation] = []
    remaining = total_budget
    for value, obligation in cycle(scored):
        if remaining <= 0:
            break
        units = min(obligation.finite_budget_units, remaining)
        allocations.append(
            CampaignAllocation(
                problem_id=obligation.problem_id,
                obligation_id=obligation.obligation_id,
                priority_score=value,
                finite_budget_units=units,
                reasons=(
                    "transparent multiplicative research-value score",
                    "finite invocation budget",
                    "allocation is not probability of mathematical truth",
                ),
            )
        )
        remaining -= units
    return tuple(allocations)


def campaign_manifest(allocations: Iterable[CampaignAllocation]) -> dict[str, object]:
    materialized = tuple(allocations)
    return {
        "allocation_count": len(materialized),
        "allocated_units": sum(item.finite_budget_units for item in materialized),
        "permanent_total_cap": None,
        "priority_score_is_not_truth_probability": True,
        "solution_claimed": False,
        "allocations": [
            {
                "problem_id": item.problem_id,
                "obligation_id": item.obligation_id,
                "priority_score": item.priority_score,
                "finite_budget_units": item.finite_budget_units,
                "reasons": list(item.reasons),
                "status": item.status,
            }
            for item in materialized
        ],
    }
