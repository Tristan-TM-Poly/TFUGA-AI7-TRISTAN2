from __future__ import annotations

from copy import deepcopy
from time import perf_counter_ns

from .models import FailureRecord, KataTask, Solver, SubmissionReport


def evaluate(
    task: KataTask,
    solver: Solver,
    *,
    measure_runtime: bool = False,
) -> SubmissionReport:
    failures: list[FailureRecord] = []
    passed = 0
    started = perf_counter_ns() if measure_runtime else None

    for case in task.cases:
        try:
            observed = solver(*deepcopy(case.args))
        except Exception as exc:  # deliberate boundary: report, do not hide
            failures.append(
                FailureRecord(
                    task_id=task.task_id,
                    case_name=case.name,
                    kind="exception",
                    expected_repr=repr(case.expected),
                    observed_repr=f"{type(exc).__name__}: {exc}",
                    input_repr=repr(case.args),
                )
            )
            continue

        if observed == case.expected:
            passed += 1
        else:
            failures.append(
                FailureRecord(
                    task_id=task.task_id,
                    case_name=case.name,
                    kind="wrong-answer",
                    expected_repr=repr(case.expected),
                    observed_repr=repr(observed),
                    input_repr=repr(case.args),
                )
            )

    runtime_ns = perf_counter_ns() - started if started is not None else None
    return SubmissionReport(
        task_id=task.task_id,
        passed=passed,
        total=len(task.cases),
        failures=tuple(failures),
        runtime_ns=runtime_ns,
    )
