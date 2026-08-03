from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .hashing import stable_id


@dataclass(frozen=True)
class FailureGenome:
    failure_id: str
    task_id: str
    symptom: str
    minimal_counterexample: str
    root_cause: str
    false_assumption: str
    mutation_operator: str
    repair: str
    regression_test: str
    recurrence_count: int = 1
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "task_id": self.task_id,
            "symptom": self.symptom,
            "minimal_counterexample": self.minimal_counterexample,
            "root_cause": self.root_cause,
            "false_assumption": self.false_assumption,
            "mutation_operator": self.mutation_operator,
            "repair": self.repair,
            "regression_test": self.regression_test,
            "recurrence_count": self.recurrence_count,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class StrategyGenome:
    strategy_id: str
    name: str
    preconditions: tuple[str, ...]
    invariant: str
    decomposition: tuple[str, ...]
    data_structures: tuple[str, ...]
    claimed_complexity: str
    failure_boundary: tuple[str, ...]
    transferable_to: tuple[str, ...]
    proof_sketch: str
    evidence_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "preconditions": list(self.preconditions),
            "invariant": self.invariant,
            "decomposition": list(self.decomposition),
            "data_structures": list(self.data_structures),
            "claimed_complexity": self.claimed_complexity,
            "failure_boundary": list(self.failure_boundary),
            "transferable_to": list(self.transferable_to),
            "proof_sketch": self.proof_sketch,
            "evidence_count": self.evidence_count,
        }


@dataclass
class NegativeMemory:
    entries: dict[str, FailureGenome] = field(default_factory=dict)

    def record(
        self,
        *,
        task_id: str,
        symptom: str,
        minimal_counterexample: str,
        root_cause: str,
        false_assumption: str,
        mutation_operator: str,
        repair: str,
        regression_test: str,
        tags: Iterable[str] = (),
    ) -> FailureGenome:
        identity = {
            "task_id": task_id,
            "root_cause": root_cause,
            "false_assumption": false_assumption,
            "mutation_operator": mutation_operator,
        }
        failure_id = stable_id("mminus", identity, length=20)
        previous = self.entries.get(failure_id)
        genome = FailureGenome(
            failure_id=failure_id,
            task_id=task_id,
            symptom=symptom,
            minimal_counterexample=minimal_counterexample,
            root_cause=root_cause,
            false_assumption=false_assumption,
            mutation_operator=mutation_operator,
            repair=repair,
            regression_test=regression_test,
            recurrence_count=(previous.recurrence_count + 1 if previous else 1),
            tags=tuple(sorted(set(tags))),
        )
        self.entries[failure_id] = genome
        return genome

    def related(self, tag: str) -> tuple[FailureGenome, ...]:
        return tuple(
            entry
            for entry in sorted(self.entries.values(), key=lambda item: item.failure_id)
            if tag in entry.tags
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.entries),
            "entries": [self.entries[key].to_dict() for key in sorted(self.entries)],
        }


@dataclass
class PositiveMemory:
    entries: dict[str, StrategyGenome] = field(default_factory=dict)

    def record(
        self,
        *,
        name: str,
        preconditions: Iterable[str],
        invariant: str,
        decomposition: Iterable[str],
        data_structures: Iterable[str],
        claimed_complexity: str,
        failure_boundary: Iterable[str],
        transferable_to: Iterable[str],
        proof_sketch: str,
    ) -> StrategyGenome:
        identity = {
            "name": name,
            "invariant": invariant,
            "claimed_complexity": claimed_complexity,
        }
        strategy_id = stable_id("mplus", identity, length=20)
        previous = self.entries.get(strategy_id)
        genome = StrategyGenome(
            strategy_id=strategy_id,
            name=name,
            preconditions=tuple(preconditions),
            invariant=invariant,
            decomposition=tuple(decomposition),
            data_structures=tuple(data_structures),
            claimed_complexity=claimed_complexity,
            failure_boundary=tuple(failure_boundary),
            transferable_to=tuple(transferable_to),
            proof_sketch=proof_sketch,
            evidence_count=(previous.evidence_count + 1 if previous else 1),
        )
        self.entries[strategy_id] = genome
        return genome

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.entries),
            "entries": [self.entries[key].to_dict() for key in sorted(self.entries)],
        }
