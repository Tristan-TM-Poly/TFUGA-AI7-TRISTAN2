import json
from pathlib import Path

from omega_re_t.baseline_execution import BaselineCase, execute_baseline
from omega_re_t.r04_cli import main


def test_baseline_execution_separates_materialization_from_execution():
    report = execute_baseline(
        baseline="identity",
        cases=[BaselineCase("c0", {"x": 1}, 1)],
        evaluator=lambda payload: payload["x"],
        logical_cases=1024,
        materialized_cases=1024,
    )
    assert report.logical_cases == 1024
    assert report.materialized_cases == 1024
    assert report.executed_cases == 1
    assert report.software_tested_cases == 1
    assert report.scientifically_verified_cases == 0
    assert report.passed_cases == 1


def test_baseline_errors_are_receipted_not_hidden():
    report = execute_baseline(
        baseline="broken",
        cases=[BaselineCase("c0", {}, 0)],
        evaluator=lambda payload: 1 / 0,
    )
    assert report.failed_cases == 1
    assert report.executions[0].error.startswith("ZeroDivisionError")


def test_r04_cli_all_is_deterministic(tmp_path: Path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    assert main(["all", "--output", str(first)]) == 0
    assert main(["all", "--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["receipt-demo"]["valid"] is True
    assert payload["baseline-demo"]["executed_cases"] == 3
