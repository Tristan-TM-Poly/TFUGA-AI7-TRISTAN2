from __future__ import annotations

import json
import runpy
from pathlib import Path

from omega_millennium_t.r11 import compile_competition_ledger


def _bundle() -> dict:
    return runpy.run_path("tests/test_omega_problem_atlas_r11_competition_ledger.py")[
        "_build_bundle"
    ]()


def _compile(tmp_path: Path, bundle: dict) -> tuple[dict, list[dict], list[dict], list[dict]]:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / "output"
    report = compile_competition_ledger(path, output)
    plans = [
        json.loads(line)
        for line in (output / "plans.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cycles = [
        json.loads(line)
        for line in (output / "cycles.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    archives = [
        json.loads(line)
        for line in (output / "archive_benchmarks.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return report, plans, cycles, archives


def _eligibility(plans: list[dict]) -> dict:
    return next(row for row in plans if row["plan_id"] == "plan.eligibility.2026")


def test_excluded_residency_blocks_eligibility(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["cycles"][1]["eligibility"]["excluded_residencies"] = ["CA"]
    report, plans, _, _ = _compile(tmp_path, bundle)
    row = _eligibility(plans)
    assert "residency_excluded" in row["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_minimum_age_blocks_eligibility(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["plans"][0]["participant_age"] = 17
    report, plans, _, _ = _compile(tmp_path, bundle)
    assert "minimum_age_not_satisfied" in _eligibility(plans)["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_team_size_out_of_range_blocks_eligibility(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["plans"][0]["team_size"] = 5
    report, plans, _, _ = _compile(tmp_path, bundle)
    assert "team_size_out_of_range" in _eligibility(plans)["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_authorized_plan_requires_authorization_reference(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["plans"][0]["status"] = "authorized"
    report, plans, _, _ = _compile(tmp_path, bundle)
    assert "authorization_reference_missing" in _eligibility(plans)["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_plan_created_after_as_of_is_invalid(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["plans"][0]["created_at"] = "2026-08-04T12:00:00-04:00"
    report, plans, _, _ = _compile(tmp_path, bundle)
    assert "plan_created_after_as_of" in _eligibility(plans)["blockers"]
    assert report["invalid_plan_count"] >= 1


def test_missing_referenced_source_blocks_cycle(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["cycles"][1]["judging"]["judging_reference_ids"] = ["source.missing"]
    report, _, cycles, _ = _compile(tmp_path, bundle)
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert "source_reference_missing:source.missing" in active["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_invalid_deadline_order_blocks_cycle(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["cycles"][1]["submission_open"] = "2026-08-12T09:00:00-04:00"
    # Correct nested location after deliberately exercising the fixture structure.
    bundle["cycles"][1]["deadlines"]["submission_open"] = "2026-08-12T09:00:00-04:00"
    bundle["cycles"][1].pop("submission_open", None)
    report, _, cycles, _ = _compile(tmp_path, bundle)
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert "deadline_order_invalid:submission_open>submission_close" in active["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_archived_task_without_digest_is_not_exported(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["cycles"][0]["tasks"][0]["artifact_digest"] = None
    report, _, cycles, archives = _compile(tmp_path, bundle)
    old = next(row for row in cycles if row["cycle_id"] == "2025")
    assert "archive_artifact_digest_missing:task.2025.main" in old["blockers"]
    assert archives == []
    assert report["archive_benchmark_count"] == 0


def test_archived_task_with_prohibited_license_is_not_exported(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["cycles"][0]["tasks"][0]["archive_license"] = "prohibited"
    report, _, cycles, archives = _compile(tmp_path, bundle)
    old = next(row for row in cycles if row["cycle_id"] == "2025")
    assert "archive_license_not_usable:task.2025.main" in old["blockers"]
    assert archives == []
    assert report["archive_benchmark_count"] == 0


def test_result_source_from_wrong_organizer_invalidates_result(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["sources"][2]["organizer_domain"] = "other.example"
    bundle["sources"][2]["official_url"] = "https://other.example/2025/results"
    report, _, _, _ = _compile(tmp_path, bundle)
    output = tmp_path / "output"
    row = json.loads((output / "submission_receipts.jsonl").read_text(encoding="utf-8"))
    assert any(item.startswith("result_source_organizer_mismatch:") for item in row["blockers"])
    assert report["invalid_submission_receipt_count"] == 1
