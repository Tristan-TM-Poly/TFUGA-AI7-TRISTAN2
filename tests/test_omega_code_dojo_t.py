from __future__ import annotations

import json

from omega_code_dojo_t.benchmark import MUTANT_SOLVERS, run_oak_benchmark
from omega_code_dojo_t.catalog import REFERENCE_SOLVERS, original_catalog
from omega_code_dojo_t.cli import main
from omega_code_dojo_t.codewars import (
    completed_url,
    fetch_completed_page,
    fetch_profile,
    normalize_progress,
    profile_url,
)
from omega_code_dojo_t.evaluator import evaluate
from omega_code_dojo_t.mminus import MMinusLedger


def test_reference_solvers_pass_every_case() -> None:
    for task in original_catalog():
        report = evaluate(task, REFERENCE_SOLVERS[task.task_id])
        assert report.status == "PASS"
        assert report.score == 1.0
        assert not report.failures


def test_mutants_are_rejected_and_feed_mminus() -> None:
    reports = [
        evaluate(task, MUTANT_SOLVERS[task.task_id]) for task in original_catalog()
    ]
    assert all(report.status == "FAIL" for report in reports)
    ledger = MMinusLedger()
    ledger.absorb_many(reports)
    payload = ledger.to_dict()
    assert payload["total_failures"] >= len(reports)
    assert payload["unique_failure_signatures"] >= len(reports)


def test_benchmark_is_deterministic_and_oak_safe() -> None:
    first = run_oak_benchmark()
    second = run_oak_benchmark()
    assert first == second
    assert first["status"] == "CERTIFIED_SOFTWARE_FIXTURES_R0_1"
    assert first["catalog"] == {
        "tasks": 4,
        "cases": 17,
        "origins": ["omega-original"],
    }
    assert first["oak"]["references_pass"] is True
    assert first["oak"]["mutants_rejected"] is True
    assert first["claims"]["neural_training_claimed"] is False
    assert first["claims"]["hidden_tests_extracted"] is False


def test_cli_writes_json(tmp_path) -> None:
    output = tmp_path / "report.json"
    assert main(["benchmark", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "CERTIFIED_SOFTWARE_FIXTURES_R0_1"


def test_codewars_metadata_adapter_uses_public_v1_shapes() -> None:
    calls: list[str] = []

    def fake_transport(url: str) -> dict[str, object]:
        calls.append(url)
        if "completed?page=" in url:
            return {
                "totalPages": 2,
                "totalItems": 201,
                "data": [
                    {
                        "id": "kata-b",
                        "completedLanguages": ["python", "python", "rust"],
                    },
                    {"id": "kata-a", "completedLanguages": ["python"]},
                ],
            }
        return {
            "username": "Tristan User",
            "honor": 42,
            "ranks": {"overall": {"name": "6 kyu", "score": 120}},
            "codeChallenges": {"totalCompleted": 201},
        }

    profile = fetch_profile("Tristan User", transport=fake_transport)
    completed = fetch_completed_page("Tristan User", 1, transport=fake_transport)
    summary = normalize_progress(profile, completed)

    assert calls == [profile_url("Tristan User"), completed_url("Tristan User", 1)]
    assert "%20" in calls[0]
    assert summary["challenge_ids"] == ["kata-a", "kata-b"]
    assert summary["language_counts_on_page"] == {"python": 2, "rust": 1}
    assert summary["source"] == "codewars-public-api-v1-metadata"
