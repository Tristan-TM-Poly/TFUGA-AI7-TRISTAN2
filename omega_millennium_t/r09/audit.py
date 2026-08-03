from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compiler import _publication_bundle, _render_summary, evaluate_request
from .model import PromotionRequest, read_jsonl, stable_digest


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _without_digest(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {item_key: item_value for item_key, item_value in value.items() if item_key != key}


def audit_promotion_gate(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    errors: list[str] = []
    required_files = {
        "request.json",
        "checklist.jsonl",
        "promotion_receipt.json",
        "publication_bundle.json",
        "SUMMARY.md",
        "manifest.json",
        "report.json",
    }
    present = {path.name for path in output.iterdir() if path.is_file()} if output.exists() else set()
    for name in sorted(required_files - present):
        errors.append(f"missing_file:{name}")
    if errors:
        return {
            "schema": "omega-problem-promotion-audit/9",
            "valid": False,
            "errors": errors,
            "dry_run": True,
            "external_action_performed": False,
        }

    request_raw = _load_json(output / "request.json")
    try:
        request = PromotionRequest.from_dict(request_raw)
    except Exception as exc:
        errors.append(f"request_invalid:{type(exc).__name__}:{exc}")
        return {
            "schema": "omega-problem-promotion-audit/9",
            "valid": False,
            "errors": errors,
            "dry_run": True,
            "external_action_performed": False,
        }

    stored_checklist = read_jsonl(output / "checklist.jsonl")
    stored_receipt = _load_json(output / "promotion_receipt.json")
    stored_bundle = _load_json(output / "publication_bundle.json")
    stored_manifest = _load_json(output / "manifest.json")
    stored_report = _load_json(output / "report.json")
    stored_summary = (output / "SUMMARY.md").read_text(encoding="utf-8")

    evaluation = evaluate_request(request)
    expected_checklist = evaluation["checklist"]
    expected_receipt = evaluation["receipt"]
    expected_bundle = _publication_bundle(request, expected_receipt)
    expected_summary = _render_summary(request, expected_receipt)

    if stored_checklist != expected_checklist:
        errors.append("checklist_replay_mismatch")
    if stored_receipt != expected_receipt:
        errors.append("receipt_replay_mismatch")
    if stored_bundle != expected_bundle:
        errors.append("publication_bundle_replay_mismatch")
    if stored_summary != expected_summary:
        errors.append("summary_replay_mismatch")

    if stored_receipt.get("receipt_digest") != stable_digest(
        _without_digest(stored_receipt, "receipt_digest")
    ):
        errors.append("receipt_digest_invalid")
    if stored_bundle.get("bundle_digest") != stable_digest(
        _without_digest(stored_bundle, "bundle_digest")
    ):
        errors.append("publication_bundle_digest_invalid")
    if stored_manifest.get("manifest_digest") != stable_digest(
        _without_digest(stored_manifest, "manifest_digest")
    ):
        errors.append("manifest_digest_invalid")
    if stored_report.get("report_digest") != stable_digest(
        _without_digest(stored_report, "report_digest")
    ):
        errors.append("report_digest_invalid")

    expected_manifest_names = {
        "request.json",
        "checklist.jsonl",
        "promotion_receipt.json",
        "publication_bundle.json",
        "SUMMARY.md",
    }
    file_digests = stored_manifest.get("file_digests")
    if not isinstance(file_digests, dict):
        errors.append("manifest_file_digests_invalid")
        file_digests = {}
    if set(file_digests) != expected_manifest_names:
        errors.append("manifest_file_set_mismatch")
    for name in sorted(expected_manifest_names):
        path = output / name
        if path.exists():
            actual = stable_digest(path.read_text(encoding="utf-8"))
            if file_digests.get(name) != actual:
                errors.append(f"manifest_file_digest_mismatch:{name}")

    if stored_manifest.get("file_count") != len(expected_manifest_names):
        errors.append("manifest_file_count_mismatch")
    if stored_manifest.get("request_id") != request.request_id:
        errors.append("manifest_request_id_mismatch")
    if stored_manifest.get("gate_ready") != expected_receipt["gate_ready"]:
        errors.append("manifest_gate_state_mismatch")

    expected_report_fields = {
        "request_id": request.request_id,
        "gate_ready": expected_receipt["gate_ready"],
        "blocker_count": len(expected_receipt["blockers"]),
        "check_count": len(expected_checklist),
        "mandatory_check_count": sum(1 for item in expected_checklist if item["mandatory"]),
        "passed_mandatory_check_count": sum(
            1 for item in expected_checklist if item["mandatory"] and item["status"] == "passed"
        ),
        "evidence_reference_count": len(request.evidence),
        "signature_count": len(request.signatures),
        "m_minus_record_count": len(request.m_minus_records),
        "receipt_digest": expected_receipt["receipt_digest"],
        "publication_bundle_digest": expected_bundle["bundle_digest"],
        "manifest_digest": stored_manifest.get("manifest_digest"),
        "dry_run": True,
        "external_action_performed": False,
        "proof_claimed": False,
        "solution_claimed": False,
        "novelty_claimed_by_compiler": False,
        "prize_recognition_claimed": False,
    }
    for key, expected in expected_report_fields.items():
        if stored_report.get(key) != expected:
            errors.append(f"report_field_mismatch:{key}")

    forbidden_true_flags = {
        "external_action_performed",
        "submission_performed",
        "publication_performed",
        "patent_filing_performed",
        "public_disclosure_performed",
        "prize_claim_submitted",
        "prize_or_clay_recognition_inferred",
        "novelty_or_correctness_self_approved",
        "mathematical_truth_probability_claimed",
        "proof_claimed_by_gate",
        "solution_claimed_by_gate",
    }
    for key in sorted(forbidden_true_flags):
        if stored_receipt.get(key) is not False:
            errors.append(f"forbidden_receipt_flag:{key}")
    if stored_receipt.get("dry_run") is not True:
        errors.append("receipt_not_dry_run")
    if stored_bundle.get("dry_run") is not True:
        errors.append("publication_bundle_not_dry_run")
    if stored_bundle.get("external_action_performed") is not False:
        errors.append("publication_bundle_external_action_detected")

    result = {
        "schema": "omega-problem-promotion-audit/9",
        "request_id": request.request_id,
        "valid": not errors,
        "errors": sorted(set(errors)),
        "replayed_gate_ready": expected_receipt["gate_ready"],
        "replayed_blocker_count": len(expected_receipt["blockers"]),
        "checked_file_count": len(required_files),
        "dry_run": True,
        "external_action_performed": False,
        "proof_claimed": False,
        "solution_claimed": False,
        "novelty_claimed": False,
        "prize_recognition_claimed": False,
    }
    result["audit_digest"] = stable_digest(result)
    return result
