from __future__ import annotations

import copy
import json
import runpy
from pathlib import Path

from omega_millennium_t.r11 import compile_competition_ledger
from omega_millennium_t.r11.model import CompetitionCycle


def _fixtures() -> dict:
    return runpy.run_path("tests/test_omega_problem_atlas_r11_competition_ledger.py")


def _compile(tmp_path: Path, bundle: dict) -> tuple[dict, list[dict], list[dict]]:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / "output"
    report = compile_competition_ledger(path, output)
    cycles = [
        json.loads(line)
        for line in (output / "cycles.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    submissions = [
        json.loads(line)
        for line in (output / "submission_receipts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return report, cycles, submissions


def test_official_rule_url_requires_https(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["cycles"][1]["official_rule_url"] = "http://competition.example/2026/rules"
    bundle["sources"][1]["official_url"] = "http://competition.example/2026/rules"
    report, cycles, _ = _compile(tmp_path, bundle)
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert any(item.startswith("https_required:") for item in active["blockers"])
    assert active["recommendation_ready"] is False
    assert report["recommended_cycle_count"] == 0


def test_source_domain_must_match_declared_organizer(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["sources"][1]["official_url"] = "https://lookalike.example/2026/rules"
    bundle["cycles"][1]["official_rule_url"] = "https://lookalike.example/2026/rules"
    report, cycles, _ = _compile(tmp_path, bundle)
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert any(item.startswith("organizer_domain_mismatch:") for item in active["blockers"])
    assert report["recommended_cycle_count"] == 0


def test_nonfirst_recurring_cycle_requires_predecessor(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["cycles"][1]["predecessor_cycle_id"] = None
    report, cycles, _ = _compile(tmp_path, bundle)
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert "predecessor_cycle_required" in active["blockers"]
    assert report["recommended_cycle_count"] == 0


def test_predecessor_loop_blocks_cycle(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["cycles"][0]["predecessor_cycle_id"] = "2026"
    _, cycles, _ = _compile(tmp_path, bundle)
    old = next(row for row in cycles if row["cycle_id"] == "2025")
    active = next(row for row in cycles if row["cycle_id"] == "2026")
    assert "earliest_cycle_must_not_have_predecessor" in old["blockers"]
    assert "predecessor_cycle_loop" in active["blockers"] or "predecessor_cycle_loop" in old["blockers"]


def test_submission_receipt_cannot_postdate_as_of(tmp_path: Path) -> None:
    fixtures = _fixtures()
    bundle = fixtures["_build_bundle"]()
    active_digest = CompetitionCycle.from_dict(bundle["cycles"][1]).rule_digest
    bundle["submission_receipts"].append(
        {
            "receipt_id": "submission.future",
            "competition_id": "competition.fixture",
            "cycle_id": "2026",
            "submitted_at": "2026-08-04T12:00:00-04:00",
            "artifact_digest": fixtures["DIGEST_D"],
            "external_receipt_reference": "fixture://external-receipt/future",
            "rule_digest": active_digest,
            "result_status": "submitted",
            "result_reference_ids": [],
            "metadata": {"fixture": True},
        }
    )
    report, _, submissions = _compile(tmp_path, bundle)
    future = next(row for row in submissions if row["receipt_id"] == "submission.future")
    assert "submission_receipt_after_as_of" in future["blockers"]
    assert future["valid"] is False
    assert report["invalid_submission_receipt_count"] == 1


def test_external_submission_receipt_requires_uri(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["submission_receipts"][0]["external_receipt_reference"] = "local-note"
    report, _, submissions = _compile(tmp_path, bundle)
    row = submissions[0]
    assert "external_submission_receipt_uri_invalid" in row["blockers"]
    assert report["invalid_submission_receipt_count"] == 1


def test_official_result_source_after_as_of_invalidates_result(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["sources"][2]["observed_at"] = "2026-08-04T12:00:00-04:00"
    report, cycles, submissions = _compile(tmp_path, bundle)
    row = submissions[0]
    assert any(item.startswith("source_observed_after_as_of:") for item in row["blockers"])
    assert row["valid"] is False
    assert report["invalid_submission_receipt_count"] == 1
