from __future__ import annotations

import pytest

from omega_capability_os_t.github_pr_generation_r05 import (
    compile_compatibility_outcomes_r05,
    pending_outcome_inputs,
)


CANDIDATE_SHA = "c" * 40
TARGET_SHA = "t" * 40


def _r04() -> dict:
    return {
        "schema": "omega-pr-5k2n-compatibility-inspection/v0.4.0",
        "fingerprint": "f" * 64,
        "compatibility_experiment_contracts": [
            {
                "experiment_id": "compat-exp:1",
                "candidate_ref": "pr:o/r#331",
                "candidate_head_sha": CANDIDATE_SHA,
                "target_ref": "pr:o/r#452",
                "target_head_sha": TARGET_SHA,
                "residual_outputs": ["implementation", "tests"],
                "candidate_source_files": ["omega/x.py"],
                "candidate_test_files": ["tests/test_x.py"],
                "required_checks": ["check interfaces"],
                "expected_receipt_fields": ["tests_executed", "verdict"],
                "execution_authorized": False,
                "source_mutation_authorized": False,
                "reuse_authorized_before_experiment": False,
                "human_review_required": True,
                "boundary": "test obligation only",
            }
        ],
    }


def _completed(
    *,
    tests_passed: int = 3,
    tests_failed: int = 0,
    coverage: float = 1.0,
    interface_status: str = "PASS",
    regressions: tuple[str, ...] = (),
    evidence: bool = True,
    authority: bool = True,
    candidate_sha: str = CANDIDATE_SHA,
    target_sha: str = TARGET_SHA,
) -> dict:
    total = tests_passed + tests_failed
    return {
        "experiment_id": "compat-exp:1",
        "candidate_ref": "pr:o/r#331",
        "candidate_head_sha": candidate_sha,
        "target_head_sha": target_sha,
        "execution_status": "COMPLETED",
        "execution_authority_ref": "authority:human-review-1" if authority else None,
        "isolation_receipt_ref": "isolation:runner-1" if authority else None,
        "tests_executed": total,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "interface_checks": [
            {"name": "public-contract", "status": interface_status, "evidence_ref": "evidence:iface"}
        ],
        "residual_coverage": coverage,
        "regressions": list(regressions),
        "evidence_refs": ["evidence:test-run", "evidence:iface"] if evidence else [],
        "environment_fingerprint": "env:" + "e" * 32 if evidence else None,
        "source_mutation_performed": False,
    }


def test_pending_contracts_remain_unknown_hold_and_m_query():
    pending = pending_outcome_inputs(_r04())
    report = compile_compatibility_outcomes_r05(_r04(), pending)
    receipt = report["receipts"][0]
    assert receipt["execution_status"] == "NOT_EXECUTED"
    assert receipt["verdict"] == "UNKNOWN"
    assert receipt["action_candidate"] == "HOLD"
    assert receipt["memory_candidate"] == "M_QUERY_CANDIDATE"
    assert receipt["action_authorized"] is False
    assert receipt["memory_promotion_authorized"] is False


def test_full_evidence_clean_run_becomes_compatible_review_candidate_only():
    report = compile_compatibility_outcomes_r05(_r04(), [_completed()])
    receipt = report["receipts"][0]
    assert receipt["candidate_sha_fresh"] is True
    assert receipt["target_sha_fresh"] is True
    assert receipt["evidence_complete_for_promotion"] is True
    assert receipt["verdict"] == "COMPATIBLE"
    assert receipt["action_candidate"] == "REUSE_CANDIDATE"
    assert receipt["memory_candidate"] == "M_PLUS_CANDIDATE"
    assert report["automatic_reuse_authorized"] is False
    assert report["automatic_memory_promotion_authorized"] is False


def test_clean_partial_coverage_routes_to_extend_candidate_not_reuse():
    report = compile_compatibility_outcomes_r05(_r04(), [_completed(coverage=0.5)])
    receipt = report["receipts"][0]
    assert receipt["verdict"] == "PARTIAL_COMPATIBLE"
    assert receipt["action_candidate"] == "EXTEND_CANDIDATE"
    assert receipt["memory_candidate"] == "M_QUERY_CANDIDATE"


def test_failed_test_yields_scoped_incompatible_m_minus_candidate():
    report = compile_compatibility_outcomes_r05(
        _r04(), [_completed(tests_passed=2, tests_failed=1)]
    )
    receipt = report["receipts"][0]
    assert receipt["verdict"] == "INCOMPATIBLE"
    assert receipt["action_candidate"] == "REJECT_CANDIDATE"
    assert receipt["memory_candidate"] == "M_MINUS_CANDIDATE"
    assert receipt["memory_promotion_authorized"] is False


def test_interface_failure_or_regression_yields_incompatible():
    interface = compile_compatibility_outcomes_r05(
        _r04(), [_completed(interface_status="FAIL")]
    )
    regression = compile_compatibility_outcomes_r05(
        _r04(), [_completed(regressions=("breaks old API",))]
    )
    assert interface["receipts"][0]["verdict"] == "INCOMPATIBLE"
    assert regression["receipts"][0]["verdict"] == "INCOMPATIBLE"


def test_missing_execution_authority_or_evidence_keeps_unknown():
    no_authority = compile_compatibility_outcomes_r05(
        _r04(), [_completed(authority=False)]
    )
    no_evidence = compile_compatibility_outcomes_r05(
        _r04(), [_completed(evidence=False)]
    )
    assert no_authority["receipts"][0]["verdict"] == "UNKNOWN"
    assert no_evidence["receipts"][0]["verdict"] == "UNKNOWN"
    assert no_authority["receipts"][0]["evidence_complete_for_promotion"] is False
    assert no_evidence["receipts"][0]["evidence_complete_for_promotion"] is False


def test_stale_candidate_or_target_sha_blocks_promotion():
    stale_candidate = compile_compatibility_outcomes_r05(
        _r04(), [_completed(candidate_sha="d" * 40)]
    )
    stale_target = compile_compatibility_outcomes_r05(
        _r04(), [_completed(target_sha="u" * 40)]
    )
    assert stale_candidate["receipts"][0]["candidate_sha_fresh"] is False
    assert stale_candidate["receipts"][0]["verdict"] == "UNKNOWN"
    assert stale_target["receipts"][0]["target_sha_fresh"] is False
    assert stale_target["receipts"][0]["verdict"] == "UNKNOWN"


def test_test_pass_rate_and_wilson_interval_are_reported_but_not_truth_probability():
    report = compile_compatibility_outcomes_r05(_r04(), [_completed()])
    receipt = report["receipts"][0]
    assert receipt["test_pass_rate"] == 1.0
    lo, hi = receipt["test_pass_rate_wilson_95"]
    assert 0.0 <= lo <= hi <= 1.0
    assert "Wilson interval over test cases != scientific confidence interval for truth" in report["oak_boundaries"]


def test_malformed_counts_unknown_experiment_and_source_mutation_fail_closed():
    malformed = _completed()
    malformed["tests_executed"] = 4
    with pytest.raises(ValueError):
        compile_compatibility_outcomes_r05(_r04(), [malformed])

    unknown = _completed()
    unknown["experiment_id"] = "compat-exp:unknown"
    with pytest.raises(ValueError):
        compile_compatibility_outcomes_r05(_r04(), [unknown])

    mutated = _completed()
    mutated["source_mutation_performed"] = True
    with pytest.raises(ValueError):
        compile_compatibility_outcomes_r05(_r04(), [mutated])


def test_duplicate_outcomes_fail_closed_and_missing_contracts_remain_visible():
    one = _completed()
    with pytest.raises(ValueError):
        compile_compatibility_outcomes_r05(_r04(), [one, one])

    report = compile_compatibility_outcomes_r05(_r04(), [])
    assert report["outcome_receipt_count"] == 0
    assert report["missing_outcome_contract_ids"] == ["compat-exp:1"]
    assert report["automatic_reuse_authorized"] is False


def test_deterministic_receipts_never_authorize_renderer_commit_or_merge():
    left = compile_compatibility_outcomes_r05(_r04(), [_completed()])
    right = compile_compatibility_outcomes_r05(_r04(), [_completed()])
    assert left == right
    assert left["write_authority_granted"] is False
    assert left["automatic_commit_allowed"] is False
    assert left["automatic_merge_allowed"] is False
    assert left["source_renderer_authorized"] is False
    assert len(left["fingerprint"]) == 64
