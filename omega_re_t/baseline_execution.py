"""Separate software execution receipts from logical benchmark materialization."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class BaselineCase:
    case_id: str
    payload: Mapping[str, Any]
    expected: Any


@dataclass(frozen=True)
class CaseExecution:
    case_id: str
    predicted: Any
    expected: Any
    passed: bool
    error: str | None = None


@dataclass(frozen=True)
class BaselineExecutionReport:
    baseline: str
    logical_cases: int
    materialized_cases: int
    executed_cases: int
    software_tested_cases: int
    scientifically_verified_cases: int
    passed_cases: int
    failed_cases: int
    execution_digest: str
    executions: tuple[CaseExecution, ...]
    claim: str = "software_baseline_execution_only"


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def execute_baseline(
    *,
    baseline: str,
    cases: Iterable[BaselineCase],
    evaluator: Callable[[Mapping[str, Any]], Any],
    logical_cases: int | None = None,
    materialized_cases: int | None = None,
) -> BaselineExecutionReport:
    case_list = tuple(cases)
    executions: list[CaseExecution] = []
    for case in case_list:
        try:
            predicted = evaluator(case.payload)
            executions.append(
                CaseExecution(
                    case_id=case.case_id,
                    predicted=predicted,
                    expected=case.expected,
                    passed=predicted == case.expected,
                )
            )
        except Exception as exc:
            executions.append(
                CaseExecution(
                    case_id=case.case_id,
                    predicted=None,
                    expected=case.expected,
                    passed=False,
                    error=f"{type(exc).__name__}:{exc}",
                )
            )
    passed = sum(item.passed for item in executions)
    logical = len(case_list) if logical_cases is None else logical_cases
    materialized = len(case_list) if materialized_cases is None else materialized_cases
    if logical < len(case_list) or materialized < len(case_list):
        raise ValueError("logical/materialized counts cannot be below executed case count")
    digest_payload = {
        "baseline": baseline,
        "executions": [asdict(item) for item in executions],
        "logical_cases": logical,
        "materialized_cases": materialized,
    }
    return BaselineExecutionReport(
        baseline=baseline,
        logical_cases=logical,
        materialized_cases=materialized,
        executed_cases=len(executions),
        software_tested_cases=len(executions),
        scientifically_verified_cases=0,
        passed_cases=passed,
        failed_cases=len(executions) - passed,
        execution_digest=_digest(digest_payload),
        executions=tuple(executions),
    )
