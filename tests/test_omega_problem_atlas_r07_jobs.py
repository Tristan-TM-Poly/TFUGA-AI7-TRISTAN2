from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r07 import audit_job_campaign, compile_job_campaign
from omega_millennium_t.r07.job_system import replay_job
from omega_millennium_t.r07.model import load_job_bundle


def _limits(max_operations: int = 10_000) -> dict:
    return {
        "max_operations": max_operations,
        "max_output_bytes": 100_000,
        "max_input_bytes": 100_000,
    }


def _job(
    job_id: str,
    runner_kind: str,
    input_payload: dict,
    error_kind: str,
    *,
    max_operations: int = 10_000,
) -> dict:
    return {
        "job_id": job_id,
        "canonical_problem_id": "problem::fixture",
        "claim_id": f"claim::{job_id}",
        "runner_kind": runner_kind,
        "method": f"fixture method for {runner_kind}",
        "scope": "restricted fixture scope",
        "stopping_rule": "stop after deterministic built-in verifier returns",
        "deterministic_seed": 7,
        "resource_limits": _limits(max_operations),
        "error_contract": {"kind": error_kind},
        "input": input_payload,
        "license_note": "Synthetic test fixture authored for this repository.",
        "network_access": False,
        "external_execution": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }


def _write_bundle(path: Path, jobs: list[dict]) -> Path:
    payload = {
        "schema": "omega-problem-job-bundle/7",
        "campaign_id": "campaign-fixture-r07",
        "environment_lock": {
            "contract_version": "omega-problem-runners/7",
            "network_access": False,
            "arbitrary_subprocess": False,
            "runner_implementation": "python-standard-library-builtins",
        },
        "jobs": jobs,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _fixture_jobs() -> list[dict]:
    return [
        _job(
            "job.exact",
            "exact_expression",
            {"expression": "(2**20 - 1) % 31"},
            "exact",
        ),
        _job(
            "job.interval",
            "interval_polynomial",
            {"coefficients": ["1", "0", "-1"], "interval": ["-1", "2"]},
            "outward_interval",
        ),
        _job(
            "job.lean",
            "lean_skeleton",
            {"source": "theorem add_zero_fixture (n : Nat) : n + 0 = n := by simp"},
            "structural_only",
        ),
        _job(
            "job.sat",
            "sat_certificate",
            {
                "clauses": [[1, -2], [2, 3], [-3, 1]],
                "assignment": {"1": True, "2": True, "3": False},
            },
            "boolean_certificate",
        ),
    ]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_all_allowlisted_runners_produce_verified_receipts(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "bundle.json", _fixture_jobs())
    output = tmp_path / "output"
    report = compile_job_campaign(bundle, output)
    receipts = {row["job_id"]: row for row in _read_jsonl(output / "job_receipts.jsonl")}

    assert report["complete"] is True
    assert report["job_count"] == 4
    assert report["completed_job_count"] == 4
    assert report["status_counts"] == {
        "success": 4,
        "failure": 0,
        "invalid_certificate": 0,
        "blocked": 0,
    }
    assert receipts["job.exact"]["output"]["canonical"] == "0"
    assert receipts["job.exact"]["certificate_status"] == "verified_exact"
    assert receipts["job.interval"]["certificate_status"] == "verified_outward_interval"
    assert receipts["job.lean"]["output"]["kernel_checked"] is False
    assert receipts["job.lean"]["certificate_status"] == "structural_only"
    assert receipts["job.sat"]["output"]["satisfied"] is True
    assert receipts["job.sat"]["certificate_status"] == "verified_boolean_certificate"
    assert all(row["theorem_promotion_allowed"] is False for row in receipts.values())
    assert audit_job_campaign(output)["valid"] is True


def test_invalid_certificates_generate_immutable_mminus(tmp_path: Path) -> None:
    jobs = [
        _job(
            "job.bad_sat",
            "sat_certificate",
            {"clauses": [[1], [-1]], "assignment": {"1": True}},
            "boolean_certificate",
        ),
        _job(
            "job.bad_lean",
            "lean_skeleton",
            {"source": "theorem false_fixture : False := by sorry"},
            "structural_only",
        ),
    ]
    bundle = _write_bundle(tmp_path / "bundle.json", jobs)
    output = tmp_path / "output"
    report = compile_job_campaign(bundle, output)
    receipts = _read_jsonl(output / "job_receipts.jsonl")
    mminus = _read_jsonl(output / "mminus_records.jsonl")

    assert report["status_counts"]["invalid_certificate"] == 2
    assert {row["status"] for row in receipts} == {"invalid_certificate"}
    assert len(mminus) == 2
    assert all(row["immutable"] is True for row in mminus)
    assert {row["reason_type"] for row in mminus} == {"invalid_certificate"}
    assert audit_job_campaign(output)["valid"] is True


def test_partial_then_resume_matches_uninterrupted_byte_for_byte(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "bundle.json", _fixture_jobs())
    uninterrupted = tmp_path / "uninterrupted"
    resumed = tmp_path / "resumed"

    compile_job_campaign(bundle, uninterrupted)
    partial = compile_job_campaign(bundle, resumed, max_jobs=2)
    assert partial["complete"] is False
    assert partial["completed_job_count"] == 2
    assert partial["remaining_job_count"] == 2
    completed = compile_job_campaign(bundle, resumed, resume=True)
    assert completed["complete"] is True

    left_files = sorted(path.name for path in uninterrupted.iterdir() if path.is_file())
    right_files = sorted(path.name for path in resumed.iterdir() if path.is_file())
    assert left_files == right_files
    for name in left_files:
        assert (uninterrupted / name).read_bytes() == (resumed / name).read_bytes(), name
    assert audit_job_campaign(resumed)["valid"] is True


def test_replay_matches_stored_receipt(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "bundle.json", _fixture_jobs())
    output = tmp_path / "output"
    compile_job_campaign(bundle, output)
    replay = replay_job(output, "job.exact")

    assert replay["stored_receipt_found"] is True
    assert replay["matches_stored_receipt"] is True
    assert replay["network_access_used"] is False
    assert replay["external_execution_used"] is False
    assert replay["proof_claimed"] is False
    assert replay["solution_claimed"] is False


def test_policy_rejects_network_and_external_execution(tmp_path: Path) -> None:
    network_job = _fixture_jobs()[0]
    network_job["network_access"] = True
    bundle = _write_bundle(tmp_path / "network.json", [network_job])
    with pytest.raises(ValueError, match="network access is forbidden"):
        load_job_bundle(bundle)

    external_job = _fixture_jobs()[0]
    external_job["external_execution"] = True
    bundle = _write_bundle(tmp_path / "external.json", [external_job])
    with pytest.raises(ValueError, match="external execution is forbidden"):
        load_job_bundle(bundle)


def test_budget_block_is_recorded_not_silently_dropped(tmp_path: Path) -> None:
    jobs = [
        _job(
            "job.budget",
            "exact_expression",
            {"expression": "2**100000"},
            "exact",
            max_operations=1,
        )
    ]
    bundle = _write_bundle(tmp_path / "bundle.json", jobs)
    output = tmp_path / "output"
    report = compile_job_campaign(bundle, output)
    receipt = _read_jsonl(output / "job_receipts.jsonl")[0]
    mminus = _read_jsonl(output / "mminus_records.jsonl")

    assert report["status_counts"]["blocked"] == 1
    assert receipt["status"] == "blocked"
    assert receipt["output"]["error_type"] == "budget_exceeded"
    assert mminus[0]["reason_type"] == "blocked"


def test_audit_detects_receipt_tampering(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "bundle.json", _fixture_jobs())
    output = tmp_path / "output"
    compile_job_campaign(bundle, output)
    path = output / "job_receipts.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["output"]["canonical"] = "tampered"
    rows[0] = json.dumps(payload, sort_keys=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    audit = audit_job_campaign(output)
    assert audit["valid"] is False
    assert any(
        "job_receipts.jsonl: sha256 mismatch" in error
        or "receipt differs from deterministic replay" in error
        for error in audit["errors"]
    )
