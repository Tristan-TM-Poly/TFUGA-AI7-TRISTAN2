"""Bracket Spectrum: measurable parenthesization geometry."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class Leaf:
    index: int


@dataclass(frozen=True)
class Node:
    left: "BracketTree"
    right: "BracketTree"


BracketTree = Leaf | Node


@dataclass(frozen=True)
class BracketSpectrum:
    trees: tuple[BracketTree, ...]
    values: tuple[Any, ...]
    distinct_values: tuple[Any, ...]
    diameter: float

    @property
    def parenthesization_count(self) -> int:
        return len(self.trees)

    @property
    def value_count(self) -> int:
        return len(self.distinct_values)


def all_parenthesizations(n: int) -> tuple[BracketTree, ...]:
    """Generate all full binary parenthesizations of n ordered leaves.

    The count is Catalan(n-1) for n>=1.
    """

    if n < 1:
        raise ValueError("n must be >= 1")

    def rec(start: int, stop: int) -> tuple[BracketTree, ...]:
        if stop - start == 1:
            return (Leaf(start),)
        result: list[BracketTree] = []
        for split in range(start + 1, stop):
            for left in rec(start, split):
                for right in rec(split, stop):
                    result.append(Node(left, right))
        return tuple(result)

    return rec(0, n)


def evaluate_tree(
    tree: BracketTree,
    values: tuple[Any, ...],
    operation: Callable[[Any, Any], Any],
) -> Any:
    if isinstance(tree, Leaf):
        return values[tree.index]
    return operation(
        evaluate_tree(tree.left, values, operation),
        evaluate_tree(tree.right, values, operation),
    )


def _distinct(values: Iterable[Any]) -> tuple[Any, ...]:
    result: list[Any] = []
    for value in values:
        if not any(value == previous for previous in result):
            result.append(value)
    return tuple(result)


def _default_metric(left: Any, right: Any) -> float:
    return float(abs(left - right))


def bracket_spectrum(
    values: Iterable[Any],
    operation: Callable[[Any, Any], Any],
    *,
    metric: Callable[[Any, Any], float] = _default_metric,
) -> BracketSpectrum:
    values_tuple = tuple(values)
    trees = all_parenthesizations(len(values_tuple))
    evaluated = tuple(
        evaluate_tree(tree, values_tuple, operation) for tree in trees
    )
    distinct = _distinct(evaluated)
    diameter = 0.0
    for left, right in combinations(distinct, 2):
        distance = float(metric(left, right))
        if distance < 0:
            raise ValueError("metric must be non-negative")
        diameter = max(diameter, distance)
    return BracketSpectrum(
        trees=trees,
        values=evaluated,
        distinct_values=distinct,
        diameter=diameter,
    )


def associativity_defect(
    x: Any,
    y: Any,
    z: Any,
    operation: Callable[[Any, Any], Any],
    *,
    metric: Callable[[Any, Any], float] = _default_metric,
) -> float:
    """Metric form of ||(xy)z - x(yz)||."""

    return float(metric(operation(operation(x, y), z), operation(x, operation(y, z))))


def zero_triple_defect_on(
    samples: Iterable[Any],
    operation: Callable[[Any, Any], Any],
    *,
    metric: Callable[[Any, Any], float] = _default_metric,
    tolerance: float = 0.0,
) -> bool:
    """Finite-sample checker for the triple condition in theorem T2.

    Passing this test is not a proof of global associativity unless `samples`
    exhaust the carrier or a separate argument establishes sufficiency.
    """

    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    points = tuple(samples)
    return all(
        associativity_defect(x, y, z, operation, metric=metric) <= tolerance
        for x in points
        for y in points
        for z in points
    )
