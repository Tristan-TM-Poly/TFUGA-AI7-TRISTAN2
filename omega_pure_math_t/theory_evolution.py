"""Finite meta-theory mutation and comparison primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class FiniteTheory:
    name: str
    axioms: frozenset[str] = frozenset()
    definitions: frozenset[str] = frozenset()
    rules: frozenset[str] = frozenset()
    theorems: frozenset[str] = frozenset()

    def add_axiom(self, axiom: str, *, name: str | None = None) -> "FiniteTheory":
        return replace(
            self,
            name=name or f"{self.name}+axiom",
            axioms=self.axioms | {axiom},
        )

    def remove_axiom(self, axiom: str, *, name: str | None = None) -> "FiniteTheory":
        return replace(
            self,
            name=name or f"{self.name}-axiom",
            axioms=self.axioms - {axiom},
        )


def symmetric_difference_distance(
    left: FiniteTheory,
    right: FiniteTheory,
    *,
    weights: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> float:
    if len(weights) != 4 or any(weight < 0 for weight in weights):
        raise ValueError("four non-negative weights required")
    components = (
        left.axioms ^ right.axioms,
        left.definitions ^ right.definitions,
        left.rules ^ right.rules,
        left.theorems ^ right.theorems,
    )
    return sum(weight * len(component) for weight, component in zip(weights, components))


def theory_intersection(left: FiniteTheory, right: FiniteTheory, *, name: str) -> FiniteTheory:
    return FiniteTheory(
        name=name,
        axioms=left.axioms & right.axioms,
        definitions=left.definitions & right.definitions,
        rules=left.rules & right.rules,
        theorems=left.theorems & right.theorems,
    )
