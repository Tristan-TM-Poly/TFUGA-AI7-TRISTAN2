"""Diversified, budgeted and non-compensatory synergy portfolio selection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .contracts import GateDecision, GateStatus, PortfolioSelection, SynergyConstellation


@dataclass(slots=True)
class PortfolioPolicy:
    budget: float = 4.0
    max_items: int = 4
    max_per_primary_domain: int = 2
    min_heuristic_utility: float = 0.10
    diversity_bonus: float = 0.08
    dependency_bonus: float = 0.03
    prefer_human_review_eligible: bool = True
    allow_experiment_eligible: bool = True
    allow_blocked: bool = False
    protected_domains: tuple[str, ...] = ("infrastructure", "product", "knowledge", "science")

    def __post_init__(self) -> None:
        if self.budget < 0:
            raise ValueError("budget cannot be negative")
        if self.max_items < 0 or self.max_per_primary_domain < 1:
            raise ValueError("invalid portfolio cardinality")
        if self.diversity_bonus < 0 or self.dependency_bonus < 0:
            raise ValueError("bonuses cannot be negative")


def _primary_domain(item: SynergyConstellation) -> str:
    return item.domains[0] if item.domains else "unclassified"


def _selection_cost(item: SynergyConstellation) -> float:
    """Finite planning cost, not currency or exact runtime."""
    base = 0.4 + 1.6 * item.integration_cost
    risk_overhead = 0.8 * item.risk_score
    uncertainty_overhead = 0.5 * item.uncertainty
    return round(max(0.1, base + risk_overhead + uncertainty_overhead), 6)


def _rank_score(item: SynergyConstellation, selected: Sequence[SynergyConstellation], policy: PortfolioPolicy) -> float:
    selected_domains = {domain for existing in selected for domain in existing.domains}
    new_domains = set(item.domains) - selected_domains
    diversity = policy.diversity_bonus * min(3, len(new_domains))
    selected_ids = {existing.id for existing in selected}
    dependency = policy.dependency_bonus * sum(dep in selected_ids for dep in item.dependencies)
    cost = _selection_cost(item)
    return round(item.heuristic_utility + diversity + dependency - 0.04 * cost, 6)


def select_portfolio(
    constellations: Sequence[SynergyConstellation],
    decisions: Sequence[GateDecision],
    *,
    policy: PortfolioPolicy | None = None,
) -> PortfolioSelection:
    policy = policy or PortfolioPolicy()
    decision_by_id = {decision.constellation_id: decision for decision in decisions}
    blocked: list[str] = []
    candidates: list[SynergyConstellation] = []

    for item in constellations:
        decision = decision_by_id.get(item.id)
        if decision is None:
            blocked.append(item.id)
            continue
        allowed = False
        if decision.status == GateStatus.ELIGIBLE_FOR_HUMAN_REVIEW:
            allowed = True
        elif decision.status == GateStatus.ELIGIBLE_FOR_EXPERIMENT and policy.allow_experiment_eligible:
            allowed = True
        elif decision.status == GateStatus.BLOCKED and policy.allow_blocked:
            allowed = True
        if not allowed or item.heuristic_utility < policy.min_heuristic_utility:
            blocked.append(item.id)
            continue
        candidates.append(item)

    selected: list[SynergyConstellation] = []
    remaining = list(candidates)
    spent = 0.0
    domain_counts: dict[str, int] = {}
    rationale: list[str] = []

    while remaining and len(selected) < policy.max_items:
        ranked = sorted(
            remaining,
            key=lambda item: (
                -(0.05 if policy.prefer_human_review_eligible and decision_by_id[item.id].status == GateStatus.ELIGIBLE_FOR_HUMAN_REVIEW else 0.0)
                - _rank_score(item, selected, policy),
                item.id,
            ),
        )
        chosen = None
        for item in ranked:
            cost = _selection_cost(item)
            domain = _primary_domain(item)
            if spent + cost > policy.budget + 1e-9:
                continue
            if domain_counts.get(domain, 0) >= policy.max_per_primary_domain:
                continue
            chosen = item
            break
        if chosen is None:
            break
        selected.append(chosen)
        remaining.remove(chosen)
        cost = _selection_cost(chosen)
        spent += cost
        domain = _primary_domain(chosen)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        rationale.append(f"selected:{chosen.id}:utility={chosen.heuristic_utility:.3f}:cost={cost:.3f}:domain={domain}")

    selected_ids = {item.id for item in selected}
    deferred = sorted(item.id for item in candidates if item.id not in selected_ids)
    missing_domains = sorted(set(policy.protected_domains) - {domain for item in selected for domain in item.domains})
    if missing_domains:
        rationale.append("uncovered_protected_domains:" + ",".join(missing_domains))
    rationale.append("selection_is_review_only_and_non_authoritative")

    return PortfolioSelection(
        selected_ids=sorted(selected_ids),
        deferred_ids=deferred,
        blocked_ids=sorted(set(blocked)),
        total_cost=round(spent, 6),
        budget=policy.budget,
        diversity_domains=sorted({domain for item in selected for domain in item.domains}),
        rationale=rationale,
    )


def selection_costs(constellations: Sequence[SynergyConstellation]) -> dict[str, float]:
    return {item.id: _selection_cost(item) for item in constellations}
