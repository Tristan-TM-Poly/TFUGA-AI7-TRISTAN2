"""Invariant compiler primitives, obstruction tests and CVCD matrices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class Invariant:
    name: str
    extractor: Callable[[Any], Any]
    equivalent: Callable[[Any, Any], bool] = lambda a, b: a == b

    def value(self, obj: Any) -> Any:
        return self.extractor(obj)

    def obstructs_isomorphism(self, left: Any, right: Any) -> bool:
        """T3: differing preserved invariant values obstruct isomorphism.

        This function assumes the caller has justified that this invariant is
        preserved by the admissible isomorphisms in the chosen category.
        """

        return not self.equivalent(self.value(left), self.value(right))


@dataclass(frozen=True)
class InvariantComparison:
    name: str
    left_value: Any
    right_value: Any
    obstructs: bool


def compare_invariants(
    left: Any,
    right: Any,
    invariants: Iterable[Invariant],
) -> tuple[InvariantComparison, ...]:
    reports: list[InvariantComparison] = []
    for invariant in invariants:
        left_value = invariant.value(left)
        right_value = invariant.value(right)
        reports.append(
            InvariantComparison(
                name=invariant.name,
                left_value=left_value,
                right_value=right_value,
                obstructs=not invariant.equivalent(left_value, right_value),
            )
        )
    return tuple(reports)


def cvcd_matrix(
    representations: Iterable[Any],
    property_fn: Callable[[Any], Any],
    metric: Callable[[Any, Any], float],
) -> tuple[tuple[float, ...], ...]:
    """Compute D^P_ij=d(P(R_i(X)),P(R_j(X)))."""

    reps = tuple(representations)
    properties = tuple(property_fn(rep) for rep in reps)
    rows: list[tuple[float, ...]] = []
    for left in properties:
        row: list[float] = []
        for right in properties:
            distance = float(metric(left, right))
            if distance < 0:
                raise ValueError("metric must be non-negative")
            row.append(distance)
        rows.append(tuple(row))
    return tuple(rows)


def invariant_preorder(
    values_by_invariant: dict[str, tuple[Any, ...]],
    derives: Callable[[tuple[Any, ...], tuple[Any, ...]], bool],
) -> dict[str, tuple[str, ...]]:
    """Build a finite preorder I_a >= I_b when caller says b derives from a.

    `derives(a_values, b_values)` is deliberately injected: dependence is a
    mathematical claim that cannot be inferred reliably from coincident samples.
    """

    result: dict[str, tuple[str, ...]] = {}
    for name_a, values_a in values_by_invariant.items():
        result[name_a] = tuple(
            name_b
            for name_b, values_b in values_by_invariant.items()
            if derives(values_a, values_b)
        )
    return result
