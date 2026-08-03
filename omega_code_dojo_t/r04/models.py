from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping

from .hashing import sha256_hex


class ProblemStatus(str, Enum):
    QUEUED = "queued"
    SOLVED_FIXTURE = "solved_fixture"
    UNRESOLVED = "unresolved"
    BLOCKED = "blocked"


class AttemptStatus(str, Enum):
    VERIFIED = "verified"
    WRONG_ANSWER = "wrong_answer"
    EXCEPTION = "exception"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ProblemInstance:
    problem_id: str
    family_id: str
    domain: str
    difficulty: int
    seed: int
    input_payload: Mapping[str, Any]
    expected_output: Any
    invariants: tuple[str, ...]
    provenance_id: str = "omega-original-synthetic-r04"
    source_kind: str = "omega_original_synthetic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "family_id": self.family_id,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "input_payload": dict(self.input_payload),
            "expected_output": self.expected_output,
            "invariants": list(self.invariants),
            "provenance_id": self.provenance_id,
            "source_kind": self.source_kind,
        }


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    family_id: str
    name: str
    exact: bool
    claimed_complexity: str
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "family_id": self.family_id,
            "name": self.name,
            "exact": self.exact,
            "claimed_complexity": self.claimed_complexity,
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True)
class AttemptRecord:
    problem_id: str
    strategy_id: str
    attempt_index: int
    status: AttemptStatus
    observed_output: Any
    expected_output: Any
    cost_units: int
    counterexample_signature: str | None = None
    exception_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "strategy_id": self.strategy_id,
            "attempt_index": self.attempt_index,
            "status": self.status.value,
            "observed_output": self.observed_output,
            "expected_output": self.expected_output,
            "cost_units": self.cost_units,
            "counterexample_signature": self.counterexample_signature,
            "exception_type": self.exception_type,
        }


@dataclass(frozen=True)
class ResolutionRecord:
    problem: ProblemInstance
    status: ProblemStatus
    attempts: tuple[AttemptRecord, ...]
    selected_strategy_id: str | None
    proof_obligations: tuple[str, ...]

    @property
    def solved(self) -> bool:
        return self.status is ProblemStatus.SOLVED_FIXTURE

    @property
    def fallback_depth(self) -> int:
        return max(0, len(self.attempts) - 1) if self.solved else len(self.attempts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem.to_dict(),
            "status": self.status.value,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "selected_strategy_id": self.selected_strategy_id,
            "proof_obligations": list(self.proof_obligations),
            "fallback_depth": self.fallback_depth,
        }


@dataclass(frozen=True)
class ResolutionPolicy:
    problem_budget: int = 4096
    max_attempts_per_problem: int = 3
    difficulty_cycle: int = 8
    permanent_total_cap: int | None = None
    stop_below_solve_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.problem_budget <= 0:
            raise ValueError("problem_budget must be positive")
        if self.max_attempts_per_problem <= 0:
            raise ValueError("max_attempts_per_problem must be positive")
        if self.difficulty_cycle <= 0:
            raise ValueError("difficulty_cycle must be positive")
        if not 0.0 <= self.stop_below_solve_rate <= 1.0:
            raise ValueError("stop_below_solve_rate must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_budget": self.problem_budget,
            "max_attempts_per_problem": self.max_attempts_per_problem,
            "difficulty_cycle": self.difficulty_cycle,
            "permanent_total_cap": self.permanent_total_cap,
            "stop_below_solve_rate": self.stop_below_solve_rate,
        }


@dataclass(frozen=True)
class FamilyMetrics:
    family_id: str
    attempted: int
    solved: int
    total_attempts: int
    fallback_solves: int
    counterexamples: int

    @property
    def solve_rate(self) -> float:
        return self.solved / self.attempted if self.attempted else 0.0

    @property
    def attempts_per_solve(self) -> float:
        return self.total_attempts / self.solved if self.solved else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "attempted": self.attempted,
            "solved": self.solved,
            "solve_rate": self.solve_rate,
            "total_attempts": self.total_attempts,
            "attempts_per_solve": self.attempts_per_solve,
            "fallback_solves": self.fallback_solves,
            "counterexamples": self.counterexamples,
        }


@dataclass(frozen=True)
class ResolutionReceipt:
    campaign_id: str
    system_version: str
    logical_problem_space: int
    materialized_problems: int
    solved_problems: int
    unresolved_problems: int
    total_attempts: int
    total_cost_units: int
    permanent_total_cap: int | None
    records: tuple[ResolutionRecord, ...]
    family_metrics: tuple[FamilyMetrics, ...]
    claims: Mapping[str, bool]
    receipt_sha256: str = field(default="")

    @property
    def solve_rate(self) -> float:
        return self.solved_problems / self.materialized_problems if self.materialized_problems else 0.0

    def to_dict(self, *, include_hash: bool = True, include_records: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "campaign_id": self.campaign_id,
            "system_version": self.system_version,
            "logical_problem_space": self.logical_problem_space,
            "materialized_problems": self.materialized_problems,
            "solved_problems": self.solved_problems,
            "unresolved_problems": self.unresolved_problems,
            "solve_rate": self.solve_rate,
            "total_attempts": self.total_attempts,
            "total_cost_units": self.total_cost_units,
            "permanent_total_cap": self.permanent_total_cap,
            "family_metrics": [metric.to_dict() for metric in self.family_metrics],
            "claims": dict(self.claims),
        }
        if include_records:
            payload["records"] = [record.to_dict() for record in self.records]
        if include_hash:
            payload["receipt_sha256"] = self.receipt_sha256
        return payload

    def with_hash(self) -> "ResolutionReceipt":
        digest = sha256_hex(self.to_dict(include_hash=False, include_records=True))
        return replace(self, receipt_sha256=digest)

    def verify_hash(self) -> bool:
        return self.receipt_sha256 == sha256_hex(
            self.to_dict(include_hash=False, include_records=True)
        )
