"""Auditable matrix repairs that always expose the correction residual."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .linalg import Matrix, add, frobenius_norm, identity, scale, subtract, trace, transpose
from .projectors import symmetric_part


@dataclass(frozen=True)
class RepairResult:
    original: Matrix
    repaired: Matrix
    correction: Matrix
    residual_norm: float
    invariant: str
    exact_constraint_satisfied: bool


def repair_symmetry(matrix: Matrix, *, tolerance: float = 1e-12) -> RepairResult:
    repaired = symmetric_part(matrix)
    correction = subtract(repaired, matrix)
    defect = subtract(repaired, transpose(repaired))
    return RepairResult(
        original=matrix,
        repaired=repaired,
        correction=correction,
        residual_norm=frobenius_norm(correction),
        invariant="T = T^T",
        exact_constraint_satisfied=frobenius_norm(defect) <= tolerance,
    )


def repair_trace(matrix: Matrix, target: float, *, tolerance: float = 1e-12) -> RepairResult:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("trace repair requires a square matrix")
    correction = scale(identity(size), (float(target) - trace(matrix)) / size)
    repaired = add(matrix, correction)
    return RepairResult(
        original=matrix,
        repaired=repaired,
        correction=correction,
        residual_norm=frobenius_norm(correction),
        invariant=f"trace(T) = {float(target)}",
        exact_constraint_satisfied=abs(trace(repaired) - float(target)) <= tolerance,
    )


def compose_repairs(matrix: Matrix, *repairs: Callable[[Matrix], RepairResult]) -> tuple[RepairResult, ...]:
    results = []
    current = matrix
    for repair in repairs:
        result = repair(current)
        results.append(result)
        current = result.repaired
    return tuple(results)
