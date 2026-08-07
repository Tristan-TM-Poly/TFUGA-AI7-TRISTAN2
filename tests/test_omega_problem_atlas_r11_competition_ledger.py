from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from omega_millennium_t.r11 import (
    audit_competition_ledger,
    compile_competition_ledger,
    recommend_active_cycles,
)
from omega_millennium_t.r11.compiler import derive_cycle_state
from omega_millennium_t.r11.model import (
    BUNDLE_SCHEMA,
    CompetitionCycle,
    stable_digest,
)

AS_OF = "2026-08-03T18:00:00Z"
FRESH_RULE_TIME = "2026-08-02T18:00:00Z"
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def _cycle(
    cycle_id: str,
    *,
    old: bool,
    predecessor: str | None,
) -> dict:
    rule_source = f"source.rules.{cycle_id}"
    if old:
        deadlines = {
            "announced_at": "2025-01-01T09:00:00-05:00",
            "registration_open": "2025-01-05T09:00:00-05:00",
            "registration_close": "2025-01-20T23:59:00-05:00",
            "task_release": "2025-01-10T09:00:00-05:00",
            "submission_open": "2025-01-10T09:00:00-05:00",
            "submission_close": "2025-02-01T23:59:00-05:00",
            "judging_end": "2025-03-01T18:00:00-05:00",
            "archive_at": "2025-04-01T00:00:00-04:00",
        }
        artifact_digest = DIGEST_C
    else:
        deadlines = {
            "announced_at": "2026-07-01T09:00:00-04:00",
            "registration_open": "2026-07-05T09:00:00-04:00",
            "registration_close": "2026-08-01T23:59:00-04:00",
            "task_release": "2026-07-10T09:00:00-04:00",
            "submission_open": "2026-07-10T09:00:00-04:00",
            "submission_close": "2026-08-10T23:59:00-04:00",
            "judging_end": "2026-08-20T18:00:00-04:00",
            "archive_at": "2026-09-01T00:00:00-04:00",
        }
        artifact_digest = None
    return {
        "competition_id": "competition.fixture",
        "cycle_id": cycle_id,
        "title": f"Fixture Challenge {cycle_id}",
        "organizer": "Fixture Foundation",
        "organizer_domain": "competition.example",
        "official_rule_url": f"https://competition.example/{cycle_id}/rules",
        "cycle_version": "1.0",
        "timezone": "America/Montreal",
        "deadlines": deadlines,
        "eligibility": {
            "registration_required": True,
            "participation_mode": "individual_or_team",
            "team_min_size": 1,
            "team_max_size": 4,
            "minimum_age": 18,
            "maximum_age": None,
            "allowed_residencies": ["CA", "US"],
            "excluded_residencies": [],
            "affiliation_requirements": [],
            "identity_verification_required": True,
            "terms_reference_ids": [rule_source],
        },
        "licenses": {
            "data_license": "CC-BY-4.0",
            "code_license": "MIT-compatible",
            "model_license": "participant-owned",
            "external_data_policy": "allowed-if-documented",
            "open_source_obligation": "none-before-results",
            "disclosure_obligation": "winning-method-summary",
            "publication_obligation": "organizer-review-before-publication",
            "license_reference_ids": [rule_source],
        },
        "prize": {
            "amount_minor_units": 250000,
            "currency": "CAD",
            "payment_conditions": ["eligibility re-verification", "tax forms"],
            "tax_note": "Tax treatment depends on participant jurisdiction.",
            "prize_reference_ids": [rule_source],
        },
        "judging": {
            "metric": "fixture_score",
            "direction": "maximize",
            "public_leaderboard": True,
            "private_leaderboard": True,
            "leaderboard_leakage_risk": "Repeated public submissions can overfit the visible split.",
            "reproducibility_requirements": ["seed", "environment", "code digest"],
            "judging_reference_ids": [rule_source],
        },
        "tasks": [
            {
                "task_id": f"task.{cycle_id}.main",
                "title": "Finite synthetic optimization benchmark",
                "task_type": "benchmark_optimization",
                "artifact_digest": artifact_digest,
                "archive_license": "CC-BY-4.0",
                "task_reference_ids": [rule_source],
                "metadata": {"finite_fixture": True},
            }
        ],
        "source_reference_ids": [rule_source],
        "predecessor_cycle_id": predecessor,
        "metadata": {"fixture": True},
    }


def _source(cycle_id: str, *, old: bool) -> dict:
    return {
        "source_id": f"source.rules.{cycle_id}",
        "source_kind": "official_rules",
        "official_url": f"https://competition.example/{cycle_id}/rules",
        "source_digest": DIGEST_A if not old else DIGEST_B,
        "observed_at": FRESH_RULE_TIME if not old else "2025-03-15T12:00:00-04:00",
        "location": "Official rules page",
        "organizer_domain": "competition.example",
        "metadata": {"cycle_id": cycle_id},
    }


def _build_bundle() -> dict:
    old_cycle = _cycle("2025", old=True, predecessor=None)
    active_cycle = _cycle("2026", old=False, predecessor="2025")
    active_rule_digest = CompetitionCycle.from_dict(active_cycle).rule_digest
    old_rule_digest = CompetitionCycle.from_dict(old_cycle).rule_digest
    return {
        "schema": BUNDLE_SCHEMA,
        "as_of": AS_OF,
        "freshness_seconds": 172800,
        "recommendation_timezone": "America/Montreal",
        "sources": [
            _source("2025", old=True),
            _source("2026", old=False),
            {
                "source_id": "source.results.2025",
                "source_kind": "official_results",
                "official_url": "https://competition.example/2025/results",
                "source_digest": DIGEST_D,
                "observed_at": "2025-03-01T19:00:00-05:00",
                "location": "Official results table",
                "organizer_domain": "competition.example",
                "metadata": {"cycle_id": "2025"},
            },
        ],
        "cycles": [old_cycle, active_cycle],
        "plans": [
            {
                "plan_id": "plan.eligibility.2026",
                "competition_id": "competition.fixture",
                "cycle_id": "2026",
                "plan_type": "eligibility",
                "created_at": "2026-08-02T16:00:00-04:00",
                "rule_digest": active_rule_digest,
                "status": "reviewed",
                "participant_age": 26,
                "participant_residency": "CA",
                "team_size": 1,
                "assumptions": ["Residency remains CA at registration review."],
                "authorization_reference": None,
                "metadata": {"fixture": True},
            },
            {
                "plan_id": "plan.submission.2026",
                "competition_id": "competition.fixture",
                "cycle_id": "2026",
                "plan_type": "submission",
                "created_at": "2026-08-02T16:10:00-04:00",
                "rule_digest": active_rule_digest,
                "status": "draft",
                "participant_age": 26,
                "participant_residency": "CA",
                "team_size": 1,
                "assumptions": ["Artifact has not been submitted."],
                "authorization_reference": None,
                "metadata": {"fixture": True},
            },
        ],
        "submission_receipts": [
            {
                "receipt_id": "submission.2025",
                "competition_id": "competition.fixture",
                "cycle_id": "2025",
                "submitted_at": "2025-01-20T20:00:00-05:00",
                "artifact_digest": DIGEST_C,
                "external_receipt_reference": "fixture://external-receipt/2025",
                "rule_digest": old_rule_digest,
                "result_status": "winner",
                "result_reference_ids": ["source.results.2025"],
                "metadata": {"recorded_only": True},
            }
        ],
    }


def _compile(tmp_path: Path, bundle: dict, name: str = "output") -> tuple[Path, dict]:
    bundle_path = tmp_path / f"{name}.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / name
    report = compile_competition_ledger(bundle_path, output)
    return output, report


def test_active_cycle_is_recommended_from_fresh_official_rules(tmp_path: Path) -> None:
    output, report = _compile(tmp_path, _build_bundle())
    assert report["active_cycle_count"] == 1
    assert report["recommended_cycle_count"] == 1
    recommendations = json.loads((output / "recommendations.json").read_text(encoding="utf-8"))
    assert recommendations[0]["cycle_id"] == "2026"
    assert recommendations[0]["registration_performed"] is False
    assert recommendations[0]["submission_performed"] is False
    deadline = recommendations[0]["submission_close_views"]
    assert deadline["america_montreal"].endswith("-04:00")
    assert deadline["utc"] == "2026-08-11T03:59:00+00:00"
    assert audit_competition_ledger(output)["valid"] is True


def test_compilation_is_byte_deterministic(tmp_path: Path) -> None:
    bundle = _build_bundle()
    output_a, report_a = _compile(tmp_path, bundle, "a")
    output_b, report_b = _compile(tmp_path, bundle, "b")
    assert report_a == report_b
    for path in sorted(output_a.iterdir()):
        assert path.read_bytes() == (output_b / path.name).read_bytes()


def test_recommendation_reader_preserves_action_boundary(tmp_path: Path) -> None:
    output, _ = _compile(tmp_path, _build_bundle())
    result = recommend_active_cycles(output)
    assert result["recommendation_count"] == 1
    assert result["requires_new_official_verification_after_as_of"] is True
    assert result["registration_performed"] is False
    assert result["submission_performed"] is False
    assert result["winner_or_prize_guaranteed"] is False


def test_archived_cycle_becomes_licensed_training_benchmark(tmp_path: Path) -> None:
    output, report = _compile(tmp_path, _build_bundle())
    assert report["archived_cycle_count"] == 1
    assert report["archive_benchmark_count"] == 1
    row = json.loads((output / "archive_benchmarks.jsonl").read_text(encoding="utf-8"))
    assert row["cycle_id"] == "2025"
    assert row["training_benchmark_only_under_license"] is True
    assert row["open_problem_status_inherited"] is False


def test_rule_change_invalidates_old_plan(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["cycles"][1]["prize"]["amount_minor_units"] += 1
    output, report = _compile(tmp_path, bundle)
    assert report["invalid_plan_count"] >= 2
    recommendations = json.loads((output / "recommendations.json").read_text(encoding="utf-8"))
    assert recommendations == []
    plans = [json.loads(line) for line in (output / "plans.jsonl").read_text(encoding="utf-8").splitlines()]
    eligibility = next(item for item in plans if item["plan_id"] == "plan.eligibility.2026")
    assert "stale_rule_digest" in eligibility["blockers"]


def test_stale_official_rules_block_recommendation(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["sources"][1]["observed_at"] = "2026-07-01T12:00:00-04:00"
    output, report = _compile(tmp_path, bundle)
    assert report["recommended_cycle_count"] == 0
    cycle_rows = [json.loads(line) for line in (output / "cycles.jsonl").read_text(encoding="utf-8").splitlines()]
    active = next(item for item in cycle_rows if item["cycle_id"] == "2026")
    assert any(item.startswith("official_rule_source_stale:") for item in active["blockers"])


def test_official_source_after_as_of_blocks(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["sources"][1]["observed_at"] = "2026-08-04T12:00:00-04:00"
    output, _ = _compile(tmp_path, bundle)
    cycle_rows = [json.loads(line) for line in (output / "cycles.jsonl").read_text(encoding="utf-8").splitlines()]
    active = next(item for item in cycle_rows if item["cycle_id"] == "2026")
    assert any(item.startswith("official_source_after_as_of:") for item in active["blockers"])
    assert active["recommendation_ready"] is False


def test_submission_after_deadline_is_invalid(tmp_path: Path) -> None:
    bundle = _build_bundle()
    active_digest = CompetitionCycle.from_dict(bundle["cycles"][1]).rule_digest
    bundle["submission_receipts"].append(
        {
            "receipt_id": "submission.late.2026",
            "competition_id": "competition.fixture",
            "cycle_id": "2026",
            "submitted_at": "2026-08-11T00:01:00-04:00",
            "artifact_digest": DIGEST_D,
            "external_receipt_reference": "fixture://external-receipt/late",
            "rule_digest": active_digest,
            "result_status": "submitted",
            "result_reference_ids": [],
            "metadata": {"fixture": True},
        }
    )
    output, report = _compile(tmp_path, bundle)
    assert report["invalid_submission_receipt_count"] == 1
    rows = [json.loads(line) for line in (output / "submission_receipts.jsonl").read_text(encoding="utf-8").splitlines()]
    late = next(item for item in rows if item["receipt_id"] == "submission.late.2026")
    assert "submitted_after_deadline" in late["blockers"]
    assert late["submission_performed_by_ledger"] is False


def test_winner_requires_official_result_source(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["submission_receipts"][0]["result_reference_ids"] = []
    output, report = _compile(tmp_path, bundle)
    assert report["invalid_submission_receipt_count"] == 1
    row = json.loads((output / "submission_receipts.jsonl").read_text(encoding="utf-8"))
    assert "official_result_reference_missing" in row["blockers"]
    assert row["prize_payment_guaranteed"] is False


def test_recurring_cycles_are_preserved_as_separate_records(tmp_path: Path) -> None:
    output, _ = _compile(tmp_path, _build_bundle())
    rows = [json.loads(line) for line in (output / "cycles.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [row["cycle_id"] for row in rows] == ["2025", "2026"]
    assert rows[1]["predecessor_cycle_id"] == "2025"
    assert rows[0]["cycle_record_digest"] != rows[1]["cycle_record_digest"]


def test_duplicate_cycle_identity_is_rejected(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["cycles"].append(copy.deepcopy(bundle["cycles"][1]))
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate cycle identity"):
        compile_competition_ledger(path, tmp_path / "output")


def test_open_problem_semantics_are_rejected_recursively(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["cycles"][1]["tasks"][0]["metadata"]["open_problem"] = True
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden competition-ledger field"):
        compile_competition_ledger(path, tmp_path / "output")


def test_state_machine_transitions() -> None:
    cycle = CompetitionCycle.from_dict(_cycle("2026", old=False, predecessor=None))
    assert derive_cycle_state(cycle, datetime.fromisoformat("2026-06-15T12:00:00+00:00")) == "announced"
    assert derive_cycle_state(cycle, datetime.fromisoformat("2026-07-06T12:00:00+00:00")) == "active"
    assert derive_cycle_state(cycle, datetime.fromisoformat("2026-08-11T12:00:00+00:00")) == "judging"
    assert derive_cycle_state(cycle, datetime.fromisoformat("2026-08-25T12:00:00+00:00")) == "closed"
    assert derive_cycle_state(cycle, datetime.fromisoformat("2026-09-02T12:00:00+00:00")) == "archived"


def test_tampered_recommendation_fails_replay_audit(tmp_path: Path) -> None:
    output, _ = _compile(tmp_path, _build_bundle())
    path = output / "recommendations.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows[0]["title"] = "Tampered"
    path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    audit = audit_competition_ledger(output)
    assert audit["valid"] is False
    assert "artifact_replay_mismatch:recommendations.json" in audit["errors"]
