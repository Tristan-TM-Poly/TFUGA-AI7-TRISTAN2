from __future__ import annotations

from omega_research_abi_t.github_measurement_bridge import (
    adapt_pr_llmt_structural_measurements,
    issue_pr_llmt_reconstruction_blob_measurement_receipt,
)
from omega_research_abi_t import validate_receipt


def _filegraph():
    return {
        "schema": "omega-pr-llmt-target-filegraph/v0.2.0",
        "fingerprint": "g" * 64,
        "portfolio_fingerprint": "p" * 64,
        "reconstruction_pair_count": 1,
        "reconstruction_pairs": [
            {
                "source_ref": "pr:example/repo#10",
                "reconstruction_ref": "pr:example/repo#11",
            }
        ],
    }


def _requests():
    return {
        "schema": "omega-pr-llmt-measurement-requests/v0.1.0",
        "fingerprint": "r" * 64,
        "source_findings_fingerprint": "f" * 64,
        "requests": [
            {
                "request_id": "request-source",
                "target_ref": "pr:example/repo#10",
                "measurement_kind": "reconstruction_equivalence_test",
            },
            {
                "request_id": "request-reconstruction",
                "target_ref": "pr:example/repo#11",
                "measurement_kind": "reconstruction_equivalence_test",
            },
        ],
    }


def _measurements(*, outcome: str = "MATCH_FULL_CHANGED_SET", error_count: int = 0):
    match = outcome != "MISMATCH"
    return {
        "schema": "omega-pr-llmt-structural-measurements/v0.1.0",
        "fingerprint": "m" * 64,
        "source_filegraph_fingerprint": "g" * 64,
        "source_requests_fingerprint": "r" * 64,
        "pair_count": 1,
        "measurement_count": 1,
        "compared_file_count": 2 if not error_count else 1,
        "blob_match_count": 2 if match and not error_count else 1,
        "blob_mismatch_count": 1 if outcome == "MISMATCH" else 0,
        "error_count": error_count,
        "measurements": [
            {
                "measurement_id": "measurement:test",
                "outcome": outcome if not error_count else "HOLD_INCOMPLETE",
                "associated_request_ids": ["request-source", "request-reconstruction"],
                "request_satisfaction": "PARTIAL_STRUCTURAL_EVIDENCE",
                "request_fully_resolved": False,
                "supersession_authority_granted": False,
            }
        ],
        "authority": {
            "write_authority_granted": False,
            "merge_authority_granted": False,
            "supersession_authority_granted": False,
        },
    }


def test_structural_measurement_adapter_is_read_only_experiment():
    env = adapt_pr_llmt_structural_measurements(_measurements())

    assert env.graph == "experiment"
    assert env.authority == "read"
    assert env.oak_state == "HOLD"
    assert "byte identity" in env.payload["bridge_boundary"]


def test_blob_measurement_receipt_passes_for_complete_positive_measurement():
    receipt = issue_pr_llmt_reconstruction_blob_measurement_receipt(
        _filegraph(), _requests(), _measurements()
    )

    assert receipt.operator == "PR_RECONSTRUCTION_BLOB_EQUIVALENCE_MEASURE"
    assert receipt.oak_state == "PASS"
    assert receipt.authority == "read"
    assert receipt.cost == 4.0
    assert validate_receipt(receipt)["status"] == "PASS"
    assert all(check.status == "PASS" for check in receipt.invariants)
    assert "byte_identity != behavioral_equivalence" in receipt.residuals


def test_complete_mismatch_is_valid_negative_measurement_not_pipeline_failure():
    receipt = issue_pr_llmt_reconstruction_blob_measurement_receipt(
        _filegraph(), _requests(), _measurements(outcome="MISMATCH")
    )

    assert receipt.oak_state == "PASS"
    assert validate_receipt(receipt)["status"] == "PASS"
    assert all(check.status == "PASS" for check in receipt.invariants)


def test_incomplete_github_evidence_holds_measurement_receipt():
    receipt = issue_pr_llmt_reconstruction_blob_measurement_receipt(
        _filegraph(), _requests(), _measurements(error_count=1)
    )

    assert receipt.oak_state == "HOLD"
    failed = {check.name for check in receipt.invariants if check.status == "FAIL"}
    assert "github_blob_evidence_complete" in failed
    assert receipt.uncertainty == 1.0


def test_tampered_source_fingerprint_holds_measurement_receipt():
    measurements = _measurements()
    measurements["source_filegraph_fingerprint"] = "x" * 64

    receipt = issue_pr_llmt_reconstruction_blob_measurement_receipt(
        _filegraph(), _requests(), measurements
    )

    assert receipt.oak_state == "HOLD"
    failed = {check.name for check in receipt.invariants if check.status == "FAIL"}
    assert "structural_measurement_source_alignment" in failed
