"""Finite defect hierarchies for binary laws.

The module treats commutators/associators as measured objects and keeps the
choice of subtraction and metric explicit. It does not claim that the resulting
finite signatures classify an algebra globally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


Binary = Callable[[Any, Any], Any]
Subtract = Callable[[Any, Any], Any]
Metric = Callable[[Any, Any], float]


@dataclass(frozen=True)
class DefectSample:
    kind: str
    inputs: tuple[Any, ...]
    value: Any
    magnitude: float


def commutator(
    x: Any,
    y: Any,
    operation: Binary,
    *,
    subtract: Subtract = lambda a, b: a - b,
) -> Any:
    return subtract(operation(x, y), operation(y, x))


def associator(
    x: Any,
    y: Any,
    z: Any,
    operation: Binary,
    *,
    subtract: Subtract = lambda a, b: a - b,
) -> Any:
    return subtract(operation(operation(x, y), z), operation(x, operation(y, z)))


def nested_commutator(
    values: Iterable[Any],
    operation: Binary,
    *,
    subtract: Subtract = lambda a, b: a - b,
) -> Any:
    """Left-nested commutator [[...[x1,x2],x3],...]."""

    points = tuple(values)
    if len(points) < 2:
        raise ValueError("nested commutator needs at least two inputs")
    result = commutator(points[0], points[1], operation, subtract=subtract)
    for point in points[2:]:
        result = commutator(result, point, operation, subtract=subtract)
    return result


def sampled_defect_signature(
    samples: Iterable[Any],
    operation: Binary,
    *,
    metric_to_zero: Callable[[Any], float] = lambda value: float(abs(value)),
    subtract: Subtract = lambda a, b: a - b,
) -> dict[str, float]:
    """Maximum first-order commutator/associator magnitudes on a finite sample."""

    points = tuple(samples)
    max_comm = 0.0
    max_assoc = 0.0
    for x in points:
        for y in points:
            max_comm = max(
                max_comm,
                float(metric_to_zero(commutator(x, y, operation, subtract=subtract))),
            )
            for z in points:
                max_assoc = max(
                    max_assoc,
                    float(
                        metric_to_zero(
                            associator(x, y, z, operation, subtract=subtract)
                        )
                    ),
                )
    return {
        "max_commutator": max_comm,
        "max_associator": max_assoc,
    }
