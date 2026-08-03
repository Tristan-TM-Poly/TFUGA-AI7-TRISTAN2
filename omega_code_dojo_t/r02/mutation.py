from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .hashing import stable_id
from .models import TaskIR


@dataclass(frozen=True)
class MutationOperator:
    operator_id: str
    family: str
    description: str
    semantic_risk: str
    expected_countercheck: str

    def to_dict(self) -> dict[str, str]:
        return {
            "operator_id": self.operator_id,
            "family": self.family,
            "description": self.description,
            "semantic_risk": self.semantic_risk,
            "expected_countercheck": self.expected_countercheck,
        }


@dataclass(frozen=True)
class MutationOutcome:
    mutation_id: str
    task_id: str
    operator_id: str
    killed: bool
    equivalent: bool
    counterexample: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "task_id": self.task_id,
            "operator_id": self.operator_id,
            "killed": self.killed,
            "equivalent": self.equivalent,
            "counterexample": self.counterexample,
        }


SEED_OPERATORS = (
    MutationOperator("mut.off-by-one", "off_by_one", "Shift a bound by one.", "boundary", "boundary case"),
    MutationOperator("mut.comparison-flip", "comparison_flip", "Reverse one comparison.", "logic", "ordered counterexample"),
    MutationOperator("mut.branch-delete", "branch_delete", "Delete one conditional branch.", "coverage", "branch-specific input"),
    MutationOperator("mut.wrong-identity", "wrong_identity", "Replace an algebraic identity.", "algebra", "empty or neutral input"),
    MutationOperator("mut.sign-flip", "sign_flip", "Invert one arithmetic sign.", "numeric", "signed input"),
    MutationOperator("mut.index-swap", "index_swap", "Swap two indexed operands.", "indexing", "asymmetric input"),
    MutationOperator("mut.termination-change", "termination_change", "Alter a termination condition.", "termination", "minimal terminating case"),
    MutationOperator("mut.numeric-narrowing", "numeric_narrowing", "Reduce numeric range.", "overflow", "large magnitude input"),
    MutationOperator("mut.overflow", "overflow", "Use unchecked fixed-width arithmetic.", "overflow", "overflow boundary"),
    MutationOperator("mut.unstable-order", "unstable_order", "Assume unordered iteration is stable.", "nondeterminism", "reordered container"),
    MutationOperator("mut.shallow-copy", "shallow_copy", "Alias nested mutable state.", "aliasing", "nested mutation"),
    MutationOperator("mut.memo-delete", "memo_delete", "Remove memoization.", "complexity", "overlapping subproblem"),
    MutationOperator("mut.cache-alias", "cache_alias", "Use an incomplete cache key.", "state", "key collision"),
    MutationOperator("mut.inadmissible-heuristic", "inadmissible_heuristic", "Overestimate a search heuristic.", "optimality", "optimality witness"),
    MutationOperator("mut.empty-case-delete", "empty_case_delete", "Remove explicit empty handling.", "boundary", "empty input"),
    MutationOperator("mut.boundary-shift", "boundary_shift", "Move a threshold boundary.", "boundary", "threshold neighbor"),
)


class MutationRegistry:
    def __init__(self, operators: Iterable[MutationOperator] = SEED_OPERATORS) -> None:
        self._operators = {operator.family: operator for operator in operators}
        if not self._operators:
            raise ValueError("at least one mutation operator is required")

    def get(self, family: str) -> MutationOperator:
        try:
            return self._operators[family]
        except KeyError:
            return MutationOperator(
                operator_id=f"mut.generated.{family}",
                family=family,
                description=f"Generated placeholder operator for {family}.",
                semantic_risk="unknown",
                expected_countercheck="generated adversarial case",
            )

    def evaluate_fixture(self, task: TaskIR, family: str) -> MutationOutcome:
        operator = self.get(family)
        digest = stable_id("mutation", [task.task_id, operator.operator_id], length=12)
        killed = family in self._operators
        return MutationOutcome(
            mutation_id=digest,
            task_id=task.task_id,
            operator_id=operator.operator_id,
            killed=killed,
            equivalent=False,
            counterexample=(operator.expected_countercheck if killed else None),
        )

    @staticmethod
    def score(outcomes: Iterable[MutationOutcome]) -> float:
        material = [outcome for outcome in outcomes if not outcome.equivalent]
        if not material:
            return 0.0
        return sum(outcome.killed for outcome in material) / len(material)
