from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r07 import audit_job_campaign, compile_job_campaign
from omega_millennium_t.r07.cli import _resolve_campaign_dir


def _job(expression: str = "1 + 1", error_kind: str = "exact") -> dict:
    return {
        "job_id": "job.exact",
        "canonical_problem_id": "problem::fixture",
        "claim_id": "claim::fixture",
        "runner_kind": "exact_expression",
        "method": "exact arithmetic fixture",
        "scope": "restricted fixture",
        "stopping_rule": "stop after deterministic verifier",
        "deterministic_seed": 0,
        "resource_limits": {
            "max_operations": 1000,
            "max_output_bytes": 10000,
            "max_input_bytes": 10000,
        },
        "error_contract": {"kind": error_kind},
        "input": {"expression": expression},
        "license_note": "Synthetic test fixture.",
        "network_access": False,
        "external_execution": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }


def _bundle(path: Path, *, campaign_id: str = "campaign-hardening", job: dict | None = None) -> Path:
    payload = {
        "schema": "omega-problem-job-bundle/7",
        "campaign_id": campaign_id,
        "environment_lock": {
            "contract_version": "omega-problem-runners/7",
            "network_access": False,
            "arbitrary_subprocess": False,
            "runner_implementation": "python-standard-library-builtins",
        },
        "jobs": [job or _job()],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_runner_error_contract_mismatch_is_rejected(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path / "bundle.json", job=_job(error_kind="structural_only"))
    with pytest.raises(ValueError, match="requires error_contract.kind='exact'"):
        compile_job_campaign(bundle, tmp_path / "output")


def test_arbitrary_python_syntax_fails_without_execution(tmp_path: Path) -> None:
    bundle = _bundle(
        tmp_path / "bundle.json",
        job=_job("__import__('pathlib').Path('owned').write_text('bad')"),
    )
    output = tmp_path / "output"
    report = compile_job_campaign(bundle, output)
    receipt = _read_jsonl(output / "job_receipts.jsonl")[0]

    assert report["status_counts"]["failure"] == 1
    assert receipt["status"] == "failure"
    assert "forbidden exact-expression syntax" in receipt["stderr"]
    assert not (tmp_path / "owned").exists()
    assert receipt["network_access"] is False
    assert receipt["external_execution"] is False
    assert audit_job_campaign(output)["valid"] is True


def test_resume_rejects_changed_bundle(tmp_path: Path) -> None:
    original = _bundle(tmp_path / "original.json", campaign_id="campaign-resume")
    output = tmp_path / "output"
    compile_job_campaign(original, output, max_jobs=0)

    changed_job = _job("2 + 2")
    changed = _bundle(tmp_path / "changed.json", campaign_id="campaign-resume", job=changed_job)
    with pytest.raises(ValueError, match="checkpoint bundle digest mismatch"):
        compile_job_campaign(changed, output, resume=True)


def test_campaign_id_resolution_finds_exactly_one_local_campaign(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path / "bundle.json", campaign_id="campaign-locate")
    campaign_dir = tmp_path / "nested" / "campaign"
    compile_job_campaign(bundle, campaign_dir)

    assert _resolve_campaign_dir("campaign-locate", tmp_path) == campaign_dir
    with pytest.raises(ValueError, match="0 matches"):
        _resolve_campaign_dir("missing-campaign", tmp_path)


def test_audit_reconstructs_bundle_digest(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path / "bundle.json")
    output = tmp_path / "output"
    compile_job_campaign(bundle, output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bundle_digest"] = "0" * 64
    manifest["digest"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = audit_job_campaign(output)
    assert audit["valid"] is False
    assert any("bundle digest does not match" in error for error in audit["errors"])
