from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compiler import _manifest, evaluate_bundle
from .model import LedgerBundle, stable_digest


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain an object")
        rows.append(value)
    return rows


def audit_competition_ledger(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "request.json",
        "sources.jsonl",
        "cycles.jsonl",
        "plans.jsonl",
        "submission_receipts.jsonl",
        "recommendations.json",
        "archive_benchmarks.jsonl",
        "manifest.json",
        "report.json",
    }
    present = {path.name for path in output.iterdir() if path.is_file()} if output.exists() else set()
    errors = [f"missing_file:{name}" for name in sorted(required - present)]
    if errors:
        return {
            "schema": "omega-competition-ledger-audit/11",
            "valid": False,
            "errors": errors,
            "registration_performed": False,
            "submission_performed": False,
        }

    request_raw = _load_json(output / "request.json")
    try:
        bundle = LedgerBundle.from_dict(request_raw)
    except Exception as exc:
        return {
            "schema": "omega-competition-ledger-audit/11",
            "valid": False,
            "errors": [f"request_invalid:{type(exc).__name__}:{exc}"],
            "registration_performed": False,
            "submission_performed": False,
        }

    evaluation = evaluate_bundle(bundle)
    expected = {
        "sources.jsonl": [item.to_dict() for item in bundle.sources],
        "cycles.jsonl": evaluation["cycle_rows"],
        "plans.jsonl": evaluation["plan_rows"],
        "submission_receipts.jsonl": evaluation["submission_rows"],
        "recommendations.json": evaluation["recommendations"],
        "archive_benchmarks.jsonl": evaluation["archive_rows"],
    }
    stored = {
        "sources.jsonl": _load_jsonl(output / "sources.jsonl"),
        "cycles.jsonl": _load_jsonl(output / "cycles.jsonl"),
        "plans.jsonl": _load_jsonl(output / "plans.jsonl"),
        "submission_receipts.jsonl": _load_jsonl(output / "submission_receipts.jsonl"),
        "recommendations.json": _load_json(output / "recommendations.json"),
        "archive_benchmarks.jsonl": _load_jsonl(output / "archive_benchmarks.jsonl"),
    }
    for name in sorted(expected):
        if stored[name] != expected[name]:
            errors.append(f"artifact_replay_mismatch:{name}")

    expected_manifest = _manifest(bundle, evaluation)
    stored_manifest = _load_json(output / "manifest.json")
    if stored_manifest != expected_manifest:
        errors.append("manifest_replay_mismatch")
    if stored_manifest.get("manifest_digest") != stable_digest(
        {key: value for key, value in stored_manifest.items() if key != "manifest_digest"}
    ):
        errors.append("manifest_digest_invalid")

    expected_report = {
        "schema": "omega-competition-ledger-report/11",
        "as_of": bundle.as_of,
        "cycle_count": len(bundle.cycles),
        "active_cycle_count": sum(1 for row in evaluation["cycle_rows"] if row["state"] == "active"),
        "recommended_cycle_count": len(evaluation["recommendations"]),
        "archived_cycle_count": sum(1 for row in evaluation["cycle_rows"] if row["state"] == "archived"),
        "archive_benchmark_count": len(evaluation["archive_rows"]),
        "invalid_plan_count": sum(1 for row in evaluation["plan_rows"] if not row["valid"]),
        "invalid_submission_receipt_count": sum(
            1 for row in evaluation["submission_rows"] if not row["valid"]
        ),
        "global_blockers": evaluation["global_blockers"],
        "manifest_digest": expected_manifest["manifest_digest"],
        "registration_performed": False,
        "submission_performed": False,
        "payment_performed": False,
        "winner_or_prize_guaranteed": False,
        "open_problem_status_inherited": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    expected_report["report_digest"] = stable_digest(expected_report)
    stored_report = _load_json(output / "report.json")
    if stored_report != expected_report:
        errors.append("report_replay_mismatch")
    if stored_report.get("report_digest") != stable_digest(
        {key: value for key, value in stored_report.items() if key != "report_digest"}
    ):
        errors.append("report_digest_invalid")

    for row in stored["cycles.jsonl"]:
        if row.get("open_problem_status_inherited") is not False:
            errors.append(f"cycle_open_problem_semantics_detected:{row.get('cycle_id')}")
        if row.get("registration_performed") is not False:
            errors.append(f"cycle_registration_action_detected:{row.get('cycle_id')}")
        if row.get("submission_performed") is not False:
            errors.append(f"cycle_submission_action_detected:{row.get('cycle_id')}")
    for row in stored["recommendations.json"]:
        if row.get("registration_performed") is not False:
            errors.append("recommendation_registration_action_detected")
        if row.get("submission_performed") is not False:
            errors.append("recommendation_submission_action_detected")
        if row.get("recommendation_is_not_registration_or_submission") is not True:
            errors.append("recommendation_boundary_missing")
    for row in stored["archive_benchmarks.jsonl"]:
        if row.get("open_problem_status_inherited") is not False:
            errors.append("archive_open_problem_semantics_detected")
        if row.get("training_benchmark_only_under_license") is not True:
            errors.append("archive_license_boundary_missing")

    result = {
        "schema": "omega-competition-ledger-audit/11",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "cycle_count": len(bundle.cycles),
        "recommendation_count": len(evaluation["recommendations"]),
        "archive_benchmark_count": len(evaluation["archive_rows"]),
        "registration_performed": False,
        "submission_performed": False,
        "payment_performed": False,
        "open_problem_status_inherited": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    result["audit_digest"] = stable_digest(result)
    return result
