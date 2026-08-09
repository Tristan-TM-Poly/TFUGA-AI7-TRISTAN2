"""Exact finite proof-library compression benchmark.

Given alternative lemma sets for each target theorem, search the smallest shared
lemma library that contains at least one complete proof support for every target.
This is finite combinatorial optimization, not a claim about general proof
complexity or Kolmogorov complexity.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import inf
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ProofSupport:
    theorem: str
    lemmas: frozenset[str]


@dataclass(frozen=True)
class CompressedProofLibrary:
    lemmas: frozenset[str]
    cost: float
    selected_supports: tuple[ProofSupport, ...]


def minimum_proof_library(
    supports: Iterable[ProofSupport],
    *,
    lemma_costs: Mapping[str, float] | None = None,
) -> CompressedProofLibrary | None:
    """Exhaustively minimize shared lemma cost over a finite support catalogue."""

    items = tuple(supports)
    if not items:
        return CompressedProofLibrary(frozenset(), 0.0, ())
    by_theorem: dict[str, list[ProofSupport]] = {}
    universe: set[str] = set()
    for support in items:
        by_theorem.setdefault(support.theorem, []).append(support)
        universe |= set(support.lemmas)

    costs = {lemma: 1.0 for lemma in universe}
    if lemma_costs is not None:
        for lemma, value in lemma_costs.items():
            if value < 0:
                raise ValueError("lemma costs must be non-negative")
            if lemma in universe:
                costs[lemma] = float(value)

    ordered = tuple(sorted(universe))
    best: CompressedProofLibrary | None = None
    best_cost = inf
    for size in range(len(ordered) + 1):
        for combo in combinations(ordered, size):
            library = frozenset(combo)
            cost = sum(costs[lemma] for lemma in library)
            if cost > best_cost:
                continue
            selected: list[ProofSupport] = []
            feasible = True
            for theorem in sorted(by_theorem):
                candidates = [
                    support
                    for support in by_theorem[theorem]
                    if support.lemmas <= library
                ]
                if not candidates:
                    feasible = False
                    break
                selected.append(
                    min(
                        candidates,
                        key=lambda support: (
                            sum(costs[lemma] for lemma in support.lemmas),
                            len(support.lemmas),
                            tuple(sorted(support.lemmas)),
                        ),
                    )
                )
            if feasible and (
                best is None
                or cost < best_cost
                or (cost == best_cost and len(library) < len(best.lemmas))
            ):
                best = CompressedProofLibrary(library, cost, tuple(selected))
                best_cost = cost
    return best
