from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class TaskCase:
    name: str
    args: tuple[Any, ...]
    expected: Any


@dataclass(frozen=True)
class KataTask:
    task_id: str
    title: str
    function_name: str
    difficulty: int
    tags: tuple[str, ...]
    cases: tuple[TaskCase, ...]
    origin: str = "omega-original"


@dataclass(frozen=True)
class FailureRecord:
    task_id: str
    case_name: str
    kind: str
    expected_repr: str
    observed_repr: str
    input_repr: str

    @property
    def fingerprint(self) -> str:
        return f"{self.task_id}:{self.case_name}:{self.kind}"


@dataclass(frozen=True)
class SubmissionReport:
    task_id: str
    passed: int
    total: int
    failures: tuple[FailureRecord, ...] = field(default_factory=tuple)
    runtime_ns: int | None = None

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def status(self) -> str:
        return "PASS" if self.passed == self.total else "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "passed": self.passed,
            "total": self.total,
            "score": self.score,
            "runtime_ns": self.runtime_ns,
            "failures": [
                {
                    "fingerprint": failure.fingerprint,
                    "case_name": failure.case_name,
                    "kind": failure.kind,
                    "input": failure.input_repr,
                    "expected": failure.expected_repr,
                    "observed": failure.observed_repr,
                }
                for failure in self.failures
            ],
        }


Solver = Callable[..., Any]
