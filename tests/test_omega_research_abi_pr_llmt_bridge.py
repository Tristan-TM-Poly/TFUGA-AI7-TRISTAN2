from __future__ import annotations

from omega_research_abi_t import (
    adapt_pr_llmt_findings,
    adapt_pr_llmt_inspection_overlay,
    adapt_pr_llmt_inspection_plan,
    adapt_pr_llmt_measurement_requests,
    compile_pr_llmt_measurement_requests,
    issue_pr_llmt_inspection_receipt,
    issue_pr_llmt_measurement_request_receipt,
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
        "packets": [
            {
                "target_ref": "pr:example/repo#10",
                "target_number": 10,
                "head_sha": "1" * 40,
                "findings": [
                    {
                        "finding_type": "INSPECTED_REUSE_CANDIDATE",
                        "priority": 4,
                        "action": "Compare exact implementation and tests.",
                        "evidence": ["pr:example/repo#3@abc:files=2,symbols=4"],
                        "boundary": "static AST is not reusable behavior",
                    },
                    {
                        "finding_type": "NEGATIVE_MEMORY_AVAILABLE",
                        "priority": 3,
                        "action": "Consult context-bound negative memory.",
                        "evidence": ["target:prior regression"],
                        "boundary": "negative memory is not universal refutation",
                    },
                ],
            }
        ],
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


def test_findings_compile_to_deterministic_unscored_measurement_requests():
    _, _, findings = _fixtures()

    first = compile_pr_llmt_measurement_requests(findings)
    second = compile_pr_llmt_measurement_requests(findings)

    assert first == second
    assert first["schema"] == "omega-pr-llmt-measurement-requests/v0.1.0"
    assert first["request_count"] == 2
    assert first["target_count"] == 1
    assert first["downstream_policy"]["numeric_opportunity_or_voc_scores_emitted"] is False
    assert first["measurement_kind_counts"] == {
        "negative_memory_context_check": 1,
        "reuse_compatibility_test": 1,
    }
    for row in first["requests"]:
        assert row["evidence"]
        assert row["priority_is_quality_score"] is False
        quantitative = row["quantitative_inputs"]
        assert quantitative["status"] == "required-before-voc-or-optimization-scoring"
        assert all(value is None for key, value in quantitative.items() if key != "status")
        assert row["downstream_contracts"]["compute_physics_pr445"]["quantitative_scoring_ready"] is False
        assert row["downstream_contracts"]["research_self_model_pr449"]["quantitative_scoring_ready"] is False
        assert row["authority"]["write_authority_granted"] is False
        assert row["authority"]["merge_authority_granted"] is False


def test_measurement_request_portfolio_is_work_and_gets_structural_receipt():
    _, _, findings = _fixtures()
    requests = compile_pr_llmt_measurement_requests(findings)

    envelope = adapt_pr_llmt_measurement_requests(requests)
    receipt = issue_pr_llmt_measurement_request_receipt(findings, requests)
    validation = validate_receipt(receipt)

    assert envelope.graph == "work"
    assert envelope.object_type == "pr_llmt_measurement_requests"
    assert envelope.authority == "read"
    assert envelope.oak_state == "HOLD"
    assert receipt.operator == "PR_FINDINGS_TO_MEASUREMENT_REQUESTS"
    assert receipt.oak_state == "PASS"
    assert receipt.authority == "read"
    assert validation["status"] == "PASS"
    assert all(check.status == "PASS" for check in receipt.invariants)
    assert "unmeasured_quantitative_input != zero" in receipt.residuals


def test_measurement_request_receipt_holds_if_false_quantitative_readiness_is_injected():
    _, _, findings = _fixtures()
    requests = compile_pr_llmt_measurement_requests(findings)
    tampered = dict(requests)
    rows = [dict(row) for row in requests["requests"]]
    rows[0] = dict(rows[0])
    rows[0]["quantitative_inputs"] = dict(rows[0]["quantitative_inputs"])
    rows[0]["quantitative_inputs"]["expected_cost"] = 0.1
    tampered["requests"] = rows

    receipt = issue_pr_llmt_measurement_request_receipt(findings, tampered)

    assert receipt.oak_state == "HOLD"
    failed = {check.name for check in receipt.invariants if check.status == "FAIL"}
    assert "no_unmeasured_quantitative_scoring" in failed
    assert receipt.authority == "read"
