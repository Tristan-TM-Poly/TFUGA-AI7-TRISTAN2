"""Research ABI bridge for exact GitHub structural measurements."""
from __future__ import annotations

from typing import Any, Mapping

from .core import Envelope, InvariantCheck, stable_digest
from .github_memory_bridge import adapt_pr_llmt_measurement_requests
from .receipts import issue_receipt

STRUCTURAL_MEASUREMENT_SCHEMA = "omega-pr-llmt-structural-measurements/v0.1.0"
TARGET_FILEGRAPH_SCHEMA = "omega-pr-llmt-target-filegraph/v0.2.0"


def _filegraph_envelope(filegraph: Mapping[str, Any]) -> Envelope:
    body = dict(filegraph)
    if body.get("schema") != TARGET_FILEGRAPH_SCHEMA:
        raise TypeError(f"target filegraph requires schema {TARGET_FILEGRAPH_SCHEMA}")
    fingerprint = str(body.get("fingerprint") or "")
    if not fingerprint:
        body["fingerprint"] = stable_digest(body)
    return Envelope(
        graph="provenance",
        object_type="pr_llmt_target_filegraph",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=(f"portfolio:{body.get('portfolio_fingerprint')}",),
        authority="read",
        oak_state="HOLD",
    )


def adapt_pr_llmt_structural_measurements(measurements: Mapping[str, Any]) -> Envelope:
    body = dict(measurements)
    if body.get("schema") != STRUCTURAL_MEASUREMENT_SCHEMA:
        raise TypeError(f"structural measurements require schema {STRUCTURAL_MEASUREMENT_SCHEMA}")
    if not body.get("fingerprint"):
        body["fingerprint"] = stable_digest(body)
    body["source_ontology"] = (
        "omega_capability_os_t.github_pr_llmt_measurements."
        "compile_reconstruction_blob_measurements"
    )
    body["bridge_boundary"] = (
        "Git blob SHA equality proves byte identity for measured file contents only; "
        "it does not prove behavior, test success, merge readiness or supersession safety"
    )
    return Envelope(
        graph="experiment",
        object_type="pr_llmt_structural_measurements",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=tuple(
            item
            for item in (
                f"filegraph:{body.get('source_filegraph_fingerprint')}" if body.get("source_filegraph_fingerprint") else "",
                f"requests:{body.get('source_requests_fingerprint')}" if body.get("source_requests_fingerprint") else "",
            )
            if item
        ),
        authority="read",
        oak_state="HOLD",
    )


def issue_pr_llmt_reconstruction_blob_measurement_receipt(
    filegraph: Mapping[str, Any],
    requests: Mapping[str, Any],
    measurements: Mapping[str, Any],
):
    """Certify the measurement process while preserving negative outcomes.

    A complete blob mismatch is valid M- evidence and does *not* make the
    measurement procedure fail. HOLD is reserved for incomplete or misbound
    evidence, authority widening, or malformed associations.
    """
    filegraph_env = _filegraph_envelope(filegraph)
    requests_env = adapt_pr_llmt_measurement_requests(requests)
    measurement_env = adapt_pr_llmt_structural_measurements(measurements)

    source_alignment = (
        str(measurements.get("source_filegraph_fingerprint") or "")
        == str(filegraph.get("fingerprint") or "")
        and str(measurements.get("source_requests_fingerprint") or "")
        == str(requests.get("fingerprint") or "")
    )
    authority_ok = (
        measurements.get("authority", {}).get("write_authority_granted") is False
        and measurements.get("authority", {}).get("merge_authority_granted") is False
        and measurements.get("authority", {}).get("supersession_authority_granted") is False
    )
    expected_pairs = int(filegraph.get("reconstruction_pair_count", len(filegraph.get("reconstruction_pairs", []))))
    observed_pairs = int(measurements.get("pair_count", -1))
    pair_count_ok = observed_pairs == expected_pairs == len(measurements.get("measurements", []))
    error_free = int(measurements.get("error_count", 0)) == 0

    allowed_outcomes = {"MATCH_FULL_CHANGED_SET", "MATCH_SHARED_PATHS_ONLY", "MISMATCH"}
    outcomes = [str(row.get("outcome") or "") for row in measurements.get("measurements", [])]
    outcomes_complete = all(outcome in allowed_outcomes for outcome in outcomes)

    valid_request_ids = {
        str(row.get("request_id") or "")
        for row in requests.get("requests", [])
        if str(row.get("measurement_kind") or "") == "reconstruction_equivalence_test"
    }
    associated_ids = {
        str(request_id)
        for row in measurements.get("measurements", [])
        for request_id in row.get("associated_request_ids", [])
    }
    request_links_ok = associated_ids <= valid_request_ids
    no_overclaim = all(
        row.get("request_fully_resolved") is False
        and row.get("supersession_authority_granted") is False
        and row.get("request_satisfaction") == "PARTIAL_STRUCTURAL_EVIDENCE"
        for row in measurements.get("measurements", [])
    )

    invariants = (
        InvariantCheck(
            "structural_measurement_source_alignment",
            "PASS" if source_alignment else "FAIL",
            "measurement result binds the exact filegraph and measurement-request fingerprints",
        ),
        InvariantCheck(
            "read_only_authority_ceiling",
            "PASS" if authority_ok else "FAIL",
            "measurement grants no write, merge or supersession authority",
        ),
        InvariantCheck(
            "all_detected_reconstruction_pairs_observed",
            "PASS" if pair_count_ok else "FAIL",
            f"expected_pairs={expected_pairs}; observed_pairs={observed_pairs}",
        ),
        InvariantCheck(
            "github_blob_evidence_complete",
            "PASS" if error_free and outcomes_complete else "FAIL",
            f"errors={measurements.get('error_count', 0)}; outcomes={outcomes}",
        ),
        InvariantCheck(
            "measurement_request_associations_valid",
            "PASS" if request_links_ok else "FAIL",
            f"associated={len(associated_ids)}; eligible_reconstruction_requests={len(valid_request_ids)}",
        ),
        InvariantCheck(
            "partial_evidence_not_promoted_to_full_resolution",
            "PASS" if no_overclaim else "FAIL",
            "blob measurement remains partial evidence and never authorizes supersession",
        ),
    )
    oak_state = "PASS" if all(item.status == "PASS" for item in invariants) else "HOLD"

    return issue_receipt(
        operator="PR_RECONSTRUCTION_BLOB_EQUIVALENCE_MEASURE",
        inputs=(filegraph_env.ref, requests_env.ref),
        outputs=(measurement_env.ref,),
        assumptions=(
            "GitHub Contents API file sha is the Git blob SHA at the requested exact head",
            "measurement cost is represented as two read-only contents metadata lookups per compared path",
        ),
        invariants=invariants,
        evidence_refs=(measurement_env.ref,),
        residuals=(
            "byte_identity != behavioral_equivalence",
            "byte_identity != test_success",
            "byte_identity != current_base_freshness",
            "byte_identity != merge_readiness",
            "byte_identity != automatic_supersession",
            "reconstruction_measurement_requests_remain_partially_satisfied",
        ),
        uncertainty=0.0 if error_free else 1.0,
        cost=float(int(measurements.get("compared_file_count", 0)) * 2),
        authority="read",
        risk=0.0,
        rollback="discard derived read-only Git blob measurement artifacts",
        provenance=(
            "PR#448:Universal Research ABI",
            "PR#450:Target reconstruction filegraph",
            f"filegraph:{filegraph_env.object_id}",
            f"requests:{requests_env.object_id}",
            f"measurements:{measurement_env.object_id}",
        ),
        oak_state=oak_state,
    )
