from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class PortfolioCandidate:
    artifact_id: str
    evidence: float
    utility: float
    conversion: float
    reuse: float
    maintenance: float
    risk: float
    requested_minor: int
    dependencies: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
        for name in (
            "evidence",
            "utility",
            "conversion",
            "reuse",
            "maintenance",
            "risk",
        ):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.requested_minor <= 0:
            raise ValueError("requested_minor must be positive")

    @property
    def value_score(self) -> float:
        self.validate()
        positive = (
            0.35 * self.evidence
            + 0.25 * self.utility
            + 0.20 * self.conversion
            + 0.20 * self.reuse
        )
        penalty = 0.55 * self.maintenance + 0.45 * self.risk
        return max(0.0, min(1.0, positive * (1 - 0.75 * penalty)))


def dominates(left: PortfolioCandidate, right: PortfolioCandidate) -> bool:
    left.validate()
    right.validate()
    better_or_equal = (
        left.evidence >= right.evidence
        and left.utility >= right.utility
        and left.conversion >= right.conversion
        and left.reuse >= right.reuse
        and left.maintenance <= right.maintenance
        and left.risk <= right.risk
        and left.requested_minor <= right.requested_minor
    )
    strictly_better = (
        left.evidence > right.evidence
        or left.utility > right.utility
        or left.conversion > right.conversion
        or left.reuse > right.reuse
        or left.maintenance < right.maintenance
        or left.risk < right.risk
        or left.requested_minor < right.requested_minor
    )
    return better_or_equal and strictly_better


def pareto_front(
    candidates: Iterable[PortfolioCandidate],
) -> list[PortfolioCandidate]:
    items = list(candidates)
    for item in items:
        item.validate()
    return sorted(
        [
            item
            for item in items
            if not any(dominates(other, item) for other in items if other is not item)
        ],
        key=lambda item: (-item.value_score, item.artifact_id),
    )


def dependency_order(candidates: Iterable[PortfolioCandidate]) -> list[str]:
    items = {item.artifact_id: item for item in candidates}
    for item in items.values():
        item.validate()
        unknown = set(item.dependencies) - items.keys()
        if unknown:
            raise ValueError(
                f"unknown dependencies for {item.artifact_id}: {sorted(unknown)}"
            )
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            raise ValueError(f"dependency cycle detected at {identifier}")
        visiting.add(identifier)
        for dependency in sorted(items[identifier].dependencies):
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)
        order.append(identifier)

    for identifier in sorted(items):
        visit(identifier)
    return order


def allocate_portfolio(
    candidates: Iterable[PortfolioCandidate],
    *,
    budget_minor: int,
) -> list[dict[str, Any]]:
    if budget_minor < 0:
        raise ValueError("budget_minor must be non-negative")
    items = list(candidates)
    dependency_order(items)
    pending = {item.artifact_id: item for item in items}
    funded: set[str] = set()
    remaining = budget_minor
    result: list[dict[str, Any]] = []
    while pending and remaining > 0:
        ready = [
            item
            for item in pending.values()
            if set(item.dependencies).issubset(funded)
        ]
        if not ready:
            break
        ready.sort(
            key=lambda item: (
                item.value_score / item.requested_minor,
                item.value_score,
                item.artifact_id,
            ),
            reverse=True,
        )
        item = ready[0]
        grant = min(remaining, item.requested_minor)
        if grant <= 0:
            break
        funded.add(item.artifact_id)
        pending.pop(item.artifact_id)
        remaining -= grant
        result.append(
            {
                "artifact_id": item.artifact_id,
                "requested_minor": item.requested_minor,
                "granted_minor": grant,
                "value_score": round(item.value_score, 8),
                "dependencies": list(item.dependencies),
            }
        )
        if grant < item.requested_minor:
            break
    return result
