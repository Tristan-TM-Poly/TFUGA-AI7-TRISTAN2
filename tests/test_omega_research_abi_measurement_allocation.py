from __future__ import annotations

from omega_research_abi_t import (
    compile_pr_llmt_measurement_allocation,
    compile_pr_llmt_measurement_requests,
    issue_pr_llmt_measurement_allocation_receipt,
    validate_receipt,
)


def _shared_anchor_findings():
    shared = "pr:example/repo#3@abc:files=2,symbols=4"
    return {
        "schema": "omega-pr-llmt-findings/v0.2.0",
        "fingerprint": "f" * 64,
        "portfolio_fingerprint": "p" * 64,
        "filegraph_fingerprint": "g" * 64,
        "inspection_overlay_fingerprint": "o" * 64,
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
                        "evidence": [shared],
                        "boundary": "static AST is not reusable behavior",
                    }
                ],
            },
            {
                "target_ref": "pr:example/repo#11",
                "target_number": 11,
                "head_sha": "2" * 40,
                "findings": [
                    {
                        "finding_type": "INSPECTED_REUSE_CANDIDATE",
                        "priority": 4,
                        "action": "Compare exact implementation and tests.",
                        "evidence": [shared],
                        "boundary": "static AST is not reusable behavior",
                    }
                ],
            },
            {
                "target_ref": "pr:example/repo#12",
                "target_number": 12,
                "head_sha": "3" * 40,
                "findings": [
                    {
                        "finding_type": "NEGATIVE_MEMORY_AVAILABLE",
                        "priority": 3,
                        "action": "Consult context-bound negative memory.",
                        "evidence": ["target:unique prior regression"],
                        "boundary": "negative memory is not universal refutation",
                    }
                ],
            },
        ],
        "authority": {
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
    }


def test_measurement_allocation_prefers_shared_anchor_by_marginal_request_coverage():
    requests = compile_pr_llmt_measurement_requests(_shared_anchor_findings())

    allocation = compile_pr_llmt_measurement_allocation(requests, max_anchors=1)

    assert allocation["selection_policy"] == "greedy_marginal_request_evidence_coverage/v0.1"
    assert allocation["operational_budget"]["max_anchors"] == 1
    assert allocation["operational_budget"]["architecture_hard_cap"] is False
    assert allocation["selected_anchor_count"] == 1
    selected = allocation["selected_anchors"][0]
    assert selected["request_fanout"] == 2
    assert selected["target_fanout"] == 2
    assert selected["marginal_request_count"] == 2
    assert selected["marginal_target_count"] == 2
    assert allocation["projected_request_coverage_count"] == 2
    assert allocation["remaining_uncovered_request_count"] == 1
    assert allocation["projected_target_coverage_count"] == 2
    assert "EVIDENCE_ANCHOR_FANOUT != VALUE_OF_MEASUREMENT" in allocation["oak_boundaries"]


def test_measurement_allocation_is_deterministic_and_can_cover_all_without_architecture_cap():
    requests = compile_pr_llmt_measurement_requests(_shared_anchor_findings())

    first = compile_pr_llmt_measurement_allocation(requests, max_anchors=None)
    second = compile_pr_llmt_measurement_allocation(requests, max_anchors=None)

    assert first == second
    assert first["projected_request_coverage_count"] == requests["request_count"]
    assert first["remaining_uncovered_request_count"] == 0
    assert first["projected_target_coverage_count"] == requests["target_count"]
    assert first["operational_budget"]["max_anchors"] is None
    assert first["operational_budget"]["architecture_hard_cap"] is False


def test_raw_requests_are_not_falsely_routed_to_pr445_or_pr449():
    requests = compile_pr_llmt_measurement_requests(_shared_anchor_findings())
    allocation = compile_pr_llmt_measurement_allocation(requests, max_anchors=1)

    assert allocation["quantitatively_ready_request_count"] == 0
    assert allocation["quantitatively_ready_request_ids"] == []
    assert allocation["readiness"]["pr445_opportunity_evidence"]["ready_request_count"] == 0
    assert allocation["readiness"]["pr449_value_of_computation"]["ready_request_count"] == 0
    assert allocation["readiness"]["pr445_opportunity_evidence"]["blocked_request_count"] == requests["request_count"]
    assert allocation["readiness"]["pr449_value_of_computation"]["blocked_request_count"] == requests["request_count"]
    assert allocation["downstream_policy"]["numeric_opportunity_or_voc_scores_emitted"] is False
    assert allocation["downstream_policy"]["route_to_pr445_or_pr449_only_after_measured_provenance"] is True


def test_measurement_allocation_receipt_proves_structure_not_value():
    requests = compile_pr_llmt_measurement_requests(_shared_anchor_findings())
    allocation = compile_pr_llmt_measurement_allocation(requests, max_anchors=1)

    receipt = issue_pr_llmt_measurement_allocation_receipt(requests, allocation)
    validation = validate_receipt(receipt)

    assert receipt.operator == "PR_MEASUREMENT_EVIDENCE_ALLOCATION"
    assert receipt.authority == "read"
    assert receipt.oak_state == "PASS"
    assert validation["status"] == "PASS"
    assert all(check.status == "PASS" for check in receipt.invariants)
    assert "evidence_anchor_fanout != value_of_measurement" in receipt.residuals
    assert "allocation_plan != measurement_execution" in receipt.residuals


def test_measurement_allocation_receipt_holds_on_source_fingerprint_tampering():
    requests = compile_pr_llmt_measurement_requests(_shared_anchor_findings())
    allocation = compile_pr_llmt_measurement_allocation(requests, max_anchors=1)
    tampered = dict(allocation)
    tampered["source_requests_fingerprint"] = "x" * 64

    receipt = issue_pr_llmt_measurement_allocation_receipt(requests, tampered)

    assert receipt.oak_state == "HOLD"
    failed = {check.name for check in receipt.invariants if check.status == "FAIL"}
    assert "measurement_request_fingerprint_alignment" in failed
