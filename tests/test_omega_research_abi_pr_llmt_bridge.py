from __future__ import annotations

from omega_research_abi_t import (
    adapt_pr_llmt_findings,
    adapt_pr_llmt_inspection_overlay,
    adapt_pr_llmt_inspection_plan,
    issue_pr_llmt_inspection_receipt,
    validate_receipt,
)


def _fixtures():
    portfolio_fp = "a" * 64
    overlay_fp = "o" * 64
    plan = {
        "schema": "omega-pr-llmt-inspection-plan/v0.1.0",
        "fingerprint": "p" * 64,
        "portfolio_fingerprint": portfolio_fp,
        "checkpoint_fingerprint": "c" * 64,
        "selection_policy": "greedy_marginal_uncovered_packet_coverage/v0.1",
        "selected_ref_count": 2,
        "projected_packet_coverage_after_selection_count": 3,
        "remaining_uncovered_packet_count_after_selection": 0,
    }
    overlay = {
        "schema": "omega-pr-llmt-inspection-overlay/v0.1.0",
        "fingerprint": overlay_fp,
        "portfolio_fingerprint": portfolio_fp,
        "plan_fingerprint": plan["fingerprint"],
        "error_count": 0,
        "packet_coverage_after_successful_hydration": 3,
        "authority": {
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
    }
    findings = {
        "schema": "omega-pr-llmt-findings/v0.2.0",
        "fingerprint": "f" * 64,
        "portfolio_fingerprint": portfolio_fp,
        "filegraph_fingerprint": "g" * 64,
        "inspection_overlay_fingerprint": overlay_fp,
        "authority": {
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
    }
    return plan, overlay, findings


def test_pr_llmt_artifacts_reuse_universal_research_abi_without_authority_widening():
    plan, overlay, findings = _fixtures()

    plan_env = adapt_pr_llmt_inspection_plan(plan)
    overlay_env = adapt_pr_llmt_inspection_overlay(overlay)
    findings_env = adapt_pr_llmt_findings(findings)

    assert plan_env.graph == "work"
    assert overlay_env.graph == "experiment"
    assert findings_env.graph == "work"
    assert plan_env.authority == "read"
    assert overlay_env.authority == "read"
    assert findings_env.authority == "read"
    assert overlay_env.oak_state == "HOLD"
    assert findings_env.oak_state == "HOLD"
    assert "static_AST != runtime_behavior" in overlay_env.payload["bridge_boundary"]
    assert "finding != mutation_authority" in findings_env.payload["bridge_boundary"]


def test_pr_llmt_exact_inspection_issues_structural_proof_carrying_receipt():
    plan, overlay, findings = _fixtures()

    receipt = issue_pr_llmt_inspection_receipt(plan, overlay, findings)
    validation = validate_receipt(receipt)

    assert receipt.operator == "PR_LLMT_EXACT_INSPECTION"
    assert receipt.authority == "read"
    assert receipt.oak_state == "PASS"
    assert receipt.cost == 2.0
    assert validation["status"] == "PASS"
    assert all(check.status == "PASS" for check in receipt.invariants)
    assert "inspection_coverage != semantic_relevance" in receipt.residuals
    assert "structural_OAK_PASS != external_truth" in receipt.residuals
    assert len(receipt.fingerprint) == 64


def test_pr_llmt_receipt_holds_when_observed_evidence_breaks_plan_invariants():
    plan, overlay, findings = _fixtures()
    overlay = dict(overlay)
    overlay["error_count"] = 1
    overlay["packet_coverage_after_successful_hydration"] = 2

    receipt = issue_pr_llmt_inspection_receipt(plan, overlay, findings)

    assert receipt.oak_state == "HOLD"
    failed = {check.name for check in receipt.invariants if check.status == "FAIL"}
    assert "exact_hydration_error_free" in failed
    assert "projected_coverage_matches_observed" in failed
    assert receipt.authority == "read"
