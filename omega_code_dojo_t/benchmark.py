from __future__ import annotations

from collections import deque
from typing import Any, Callable

from .catalog import REFERENCE_SOLVERS, original_catalog
from .evaluator import evaluate
from .mminus import MMinusLedger


def mutant_even_values_not_squares(values: list[int]) -> int:
    return sum(value for value in values if value % 2 == 0)


def mutant_brackets_count_only(text: str) -> bool:
    return text.count("(") == text.count(")")


def mutant_rle_drops_last(text: str) -> list[tuple[str, int]]:
    if not text:
        return []
    result: list[tuple[str, int]] = []
    current = text[0]
    count = 1
    for char in text[1:]:
        if char == current:
            count += 1
        else:
            result.append((current, count))
            current, count = char, 1
    return result


def mutant_depth_first_path(
    graph: dict[str, tuple[str, ...]], start: str, goal: str
) -> list[str] | None:
    stack: deque[tuple[str, list[str]]] = deque([(start, [start])])
    visited: set[str] = set()
    while stack:
        node, path = stack.pop()
        if node == goal:
            return path
        if node in visited:
            continue
        visited.add(node)
        for neighbor in graph.get(node, ()):
            stack.append((neighbor, [*path, neighbor]))
    return None


MUTANT_SOLVERS: dict[str, Callable[..., Any]] = {
    "omega.sum-even-squares.v1": mutant_even_values_not_squares,
    "omega.balanced-brackets.v1": mutant_brackets_count_only,
    "omega.run-length-encode.v1": mutant_rle_drops_last,
    "omega.shortest-path-unweighted.v1": mutant_depth_first_path,
}


def run_oak_benchmark() -> dict[str, Any]:
    tasks = original_catalog()
    reference_reports = [
        evaluate(task, REFERENCE_SOLVERS[task.task_id]) for task in tasks
    ]
    mutant_reports = [evaluate(task, MUTANT_SOLVERS[task.task_id]) for task in tasks]
    ledger = MMinusLedger()
    ledger.absorb_many(mutant_reports)

    references_pass = all(report.status == "PASS" for report in reference_reports)
    mutants_rejected = all(report.status == "FAIL" for report in mutant_reports)
    status = (
        "CERTIFIED_SOFTWARE_FIXTURES_R0_1"
        if references_pass and mutants_rejected
        else "FAIL"
    )

    return {
        "system": "omega-code-dojo-t",
        "version": "0.1.0",
        "status": status,
        "scope": (
            "local original algorithmic fixtures; "
            "no Codewars scraping or automated submission"
        ),
        "catalog": {
            "tasks": len(tasks),
            "cases": sum(len(task.cases) for task in tasks),
            "origins": sorted({task.origin for task in tasks}),
        },
        "oak": {
            "references_pass": references_pass,
            "mutants_rejected": mutants_rejected,
            "reference_pass_rate": (
                sum(report.score for report in reference_reports)
                / len(reference_reports)
            ),
            "mutant_rejection_rate": (
                sum(report.status == "FAIL" for report in mutant_reports)
                / len(mutant_reports)
            ),
        },
        "reference_reports": [report.to_dict() for report in reference_reports],
        "mutant_reports": [report.to_dict() for report in mutant_reports],
        "m_minus": ledger.to_dict(),
        "claims": {
            "neural_training_claimed": False,
            "codewars_affiliation_claimed": False,
            "hidden_tests_extracted": False,
            "external_submissions_automated": False,
        },
    }
