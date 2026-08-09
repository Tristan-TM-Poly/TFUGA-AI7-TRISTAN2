"""Residual-of-residual towers with explicit convergence diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class ResidualStep:
    index: int
    residual: float
    modeled_residual: float
    next_residual: float

    @property
    def contraction_ratio(self) -> float:
        if self.residual == 0:
            return 0.0 if self.next_residual == 0 else float("inf")
        return abs(self.next_residual) / abs(self.residual)


def residual_tower(
    initial_residual: float,
    modeler: Callable[[float, int], float],
    steps: int,
) -> tuple[ResidualStep, ...]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    residual = float(initial_residual)
    history: list[ResidualStep] = []
    for index in range(steps):
        modeled = float(modeler(residual, index))
        next_residual = residual - modeled
        history.append(ResidualStep(index, residual, modeled, next_residual))
        residual = next_residual
    return tuple(history)


def uniformly_contracting(
    history: Iterable[ResidualStep],
    *,
    bound: float = 1.0,
) -> bool:
    if bound < 0:
        raise ValueError("bound must be non-negative")
    values = tuple(history)
    return bool(values) and all(step.contraction_ratio < bound for step in values)


def geometric_residual_bound(initial: float, contraction: float, n: int) -> float:
    if not 0 <= contraction < 1:
        raise ValueError("contraction must satisfy 0 <= q < 1")
    if n < 0:
        raise ValueError("n must be non-negative")
    return abs(initial) * contraction**n
