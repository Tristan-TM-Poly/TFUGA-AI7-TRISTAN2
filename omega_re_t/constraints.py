"""Constraint tomography and negative-space records."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class ConstraintKind(str, Enum):
    EQUALITY = "equality"
    INEQUALITY = "inequality"
    MEMBERSHIP = "membership"
    ABSENCE = "absence"
    MONOTONICITY = "monotonicity"
    CONSERVATION = "conservation"
    TEMPORAL = "temporal"
    TOPOLOGY = "topology"
    CAPACITY = "capacity"
    CUSTOM = "custom"


class Comparator(str, Enum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class Constraint:
    constraint_id: str
    field: str
    comparator: Comparator
    expected: Any = None
    kind: ConstraintKind = ConstraintKind.CUSTOM
    tolerance: float = 0.0
    weight: float = 1.0
    provenance: tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if not self.constraint_id or not self.field:
            raise ValueError("constraint_id and field required")
        if self.tolerance < 0 or self.weight < 0:
            raise ValueError("tolerance and weight cannot be negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> bool:
        exists = self.field in candidate
        actual = candidate.get(self.field)
        if self.comparator is Comparator.EXISTS:
            return exists
        if self.comparator is Comparator.ABSENT:
            return not exists
        if not exists:
            return False
        if self.comparator is Comparator.EQ:
            if isinstance(actual, (int, float)) and isinstance(
                self.expected,
                (int, float),
            ):
                return abs(actual - self.expected) <= self.tolerance
            return actual == self.expected
        if self.comparator is Comparator.NE:
            return actual != self.expected
        if self.comparator is Comparator.LT:
            return actual < self.expected
        if self.comparator is Comparator.LE:
            return actual <= self.expected + self.tolerance
        if self.comparator is Comparator.GT:
            return actual > self.expected
        if self.comparator is Comparator.GE:
            return actual + self.tolerance >= self.expected
        if self.comparator is Comparator.IN:
            return actual in self.expected
        if self.comparator is Comparator.NOT_IN:
            return actual not in self.expected
        raise AssertionError(self.comparator)


@dataclass(frozen=True, slots=True)
class ConstraintEvaluation:
    candidate_id: str
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    score: float

    @property
    def admissible(self) -> bool:
        return not self.failed


class ConstraintSet:
    def __init__(self, constraints: Iterable[Constraint] = ()):
        self._constraints: dict[str, Constraint] = {}
        for constraint in constraints:
            self.add(constraint)

    def add(self, constraint: Constraint, *, replace: bool = False) -> None:
        if constraint.constraint_id in self._constraints and not replace:
            raise KeyError(constraint.constraint_id)
        self._constraints[constraint.constraint_id] = constraint

    def __len__(self) -> int:
        return len(self._constraints)

    def __iter__(self):
        return iter(self._constraints.values())

    def evaluate(
        self,
        candidate_id: str,
        candidate: Mapping[str, Any],
    ) -> ConstraintEvaluation:
        passed: list[str] = []
        failed: list[str] = []
        passed_weight = 0.0
        total_weight = 0.0
        for constraint in self._constraints.values():
            total_weight += constraint.weight
            if constraint.evaluate(candidate):
                passed.append(constraint.constraint_id)
                passed_weight += constraint.weight
            else:
                failed.append(constraint.constraint_id)
        score = 1.0 if total_weight == 0 else passed_weight / total_weight
        return ConstraintEvaluation(
            candidate_id,
            tuple(passed),
            tuple(failed),
            score,
        )

    def filter(
        self,
        candidates: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Mapping[str, Any]]:
        return {
            candidate_id: data
            for candidate_id, data in candidates.items()
            if self.evaluate(candidate_id, data).admissible
        }

    def ranked(
        self,
        candidates: Mapping[str, Mapping[str, Any]],
    ) -> tuple[ConstraintEvaluation, ...]:
        values = [
            self.evaluate(candidate_id, data)
            for candidate_id, data in candidates.items()
        ]
        return tuple(
            sorted(
                values,
                key=lambda item: (
                    -item.score,
                    len(item.failed),
                    item.candidate_id,
                ),
            )
        )

    def intersection(self, other: "ConstraintSet") -> "ConstraintSet":
        result = ConstraintSet(self._constraints.values())
        for constraint in other:
            result.add(constraint, replace=True)
        return result

    def minimal_unsatisfied_core(
        self,
        candidate: Mapping[str, Any],
    ) -> tuple[str, ...]:
        """Return deterministic irreducible independent failed predicates."""
        failed = [
            constraint
            for constraint in self
            if not constraint.evaluate(candidate)
        ]
        seen: set[tuple[Any, ...]] = set()
        core: list[str] = []
        for constraint in failed:
            key = (
                constraint.field,
                constraint.comparator.value,
                repr(constraint.expected),
                constraint.tolerance,
            )
            if key not in seen:
                seen.add(key)
                core.append(constraint.constraint_id)
        return tuple(core)


@dataclass(frozen=True, slots=True)
class NegativeSpaceRecord:
    record_id: str
    stimulus: tuple[str, ...]
    absent_behavior: str
    repetitions: int
    confidence: float
    context: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.repetitions <= 0:
            raise ValueError("repetitions must be positive")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")

    def as_constraint(self, field: str) -> Constraint:
        return Constraint(
            self.record_id,
            field,
            Comparator.NE,
            self.absent_behavior,
            ConstraintKind.ABSENCE,
            weight=max(0.1, self.confidence),
            provenance=self.provenance,
            description=(
                f"behavior absent after {self.repetitions} repetitions"
            ),
        )


def infer_numeric_bounds(
    field: str,
    observed: Sequence[float],
    *,
    provenance: Sequence[str] = (),
) -> ConstraintSet:
    if not observed:
        raise ValueError("observed values required")
    return ConstraintSet(
        (
            Constraint(
                f"{field}-lower",
                field,
                Comparator.GE,
                min(observed),
                ConstraintKind.INEQUALITY,
                provenance=tuple(provenance),
            ),
            Constraint(
                f"{field}-upper",
                field,
                Comparator.LE,
                max(observed),
                ConstraintKind.INEQUALITY,
                provenance=tuple(provenance),
            ),
        )
    )
