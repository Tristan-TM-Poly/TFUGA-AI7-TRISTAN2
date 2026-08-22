"""Finite GO MAX / GO MIN Pareto portfolio compiler."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True, slots=True)
class GoCandidate:
    candidate_id: str
    verified_value: float
    reachability: float
    evidence_gain: float
    reuse: float
    leverage: float
    cost: float
    risk: float
    duplication: float
    proof_debt: float
    uncertainty_debt: float
    complexity: float

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.max_axes() + self.min_axes()):
            raise ValueError("GO candidate axes must be non-negative")

    def max_axes(self) -> tuple[float, ...]:
        return self.verified_value, self.reachability, self.evidence_gain, self.reuse, self.leverage

    def min_axes(self) -> tuple[float, ...]:
        return self.cost, self.risk, self.duplication, self.proof_debt, self.uncertainty_debt, self.complexity

    def power_density(self) -> float:
        numer = sum(self.max_axes())
        denom = sum(self.min_axes())
        return numer / denom if denom > 0 else (inf if numer > 0 else 0.0)


def dominates(a: GoCandidate, b: GoCandidate) -> bool:
    max_weak = all(x >= y for x, y in zip(a.max_axes(), b.max_axes()))
    min_weak = all(x <= y for x, y in zip(a.min_axes(), b.min_axes()))
    strict = any(x > y for x, y in zip(a.max_axes(), b.max_axes())) or any(
        x < y for x, y in zip(a.min_axes(), b.min_axes())
    )
    return max_weak and min_weak and strict


def pareto_front(candidates: tuple[GoCandidate, ...]) -> tuple[GoCandidate, ...]:
    ids = [c.candidate_id for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate candidate_id")
    front = [
        candidate
        for candidate in candidates
        if not any(dominates(other, candidate) for other in candidates if other != candidate)
    ]
    return tuple(sorted(front, key=lambda c: c.candidate_id))


@dataclass(frozen=True, slots=True)
class GoSelection:
    selected_id: str | None
    frontier_ids: tuple[str, ...]
    selected_power_density: float
    recurse: bool
    boundary: str = "exact only over the supplied finite candidate set and declared proxy axes"


def select_go_move(candidates: tuple[GoCandidate, ...], *, minimum_density: float = 0.0) -> GoSelection:
    if minimum_density < 0:
        raise ValueError("minimum_density must be non-negative")
    front = pareto_front(candidates)
    if not front:
        return GoSelection(None, (), 0.0, False)
    selected = max(front, key=lambda c: (c.power_density(), c.candidate_id))
    density = selected.power_density()
    return GoSelection(
        selected_id=selected.candidate_id if density > minimum_density else None,
        frontier_ids=tuple(c.candidate_id for c in front),
        selected_power_density=density,
        recurse=density > minimum_density,
    )
