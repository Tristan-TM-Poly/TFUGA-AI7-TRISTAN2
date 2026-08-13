from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from .core import Envelope, InvariantCheck, stable_digest
from .receipts import issue_receipt

GITHUB_MEMORY_R07_BOUNDARY = (
    "native_structure_bridge != semantic_equivalence_or_causal_validation"
)
PR_LLMT_R01_BOUNDARY = (
    "inspection_coverage != semantic_relevance_or_reuse_compatibility; "
    "static_AST != runtime_behavior; structural_OAK_PASS != external_truth"
)
PR_LLMT_MEASUREMENT_KIND_BY_FINDING = {
    "DECLARED_RECONSTRUCTION_PAIR": "reconstruction_equivalence_test",
    "DECLARED_RECONSTRUCTION_SOURCE": "reconstruction_equivalence_test",
    "FILE_OVERLAP_REVIEW": "shared_surface_compatibility_test",
    "LARGE_CHANGE_SURFACE": "targeted_regression_measurement",
    "INSPECTED_REUSE_CANDIDATE": "reuse_compatibility_test",
    "DEEP_EVIDENCE_GAP": "exact_head_hydration",
    "DECLARED_PRIOR_LINEAGE": "lineage_head_verification",
    "KNOWN_LATER_DESCENDANT": "downstream_impact_measurement",
    "NEGATIVE_MEMORY_AVAILABLE": "negative_memory_context_check",
}


def _payload(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("bridge value must be a dataclass or mapping")


def _require_schema(value: Mapping[str, Any], expected: str, label: str) -> dict[str, Any]:
    body = dict(value)
    if body.get("schema") != expected:
        raise TypeError(f"{label} requires schema {expected}")
    fingerprint = str(body.get("fingerprint") or "")
    if not fingerprint:
        body["fingerprint"] = stable_digest(body)
    return body


def adapt_residual_artifact_spec(spec: Any) -> Envelope:
    """Map #447 R0.4 ResidualArtifactSpec into the Work graph.

    generation_allowed remains a generation-scope observation; this adapter never
    widens it into GitHub write authority.
    """
    body = _payload(spec)
    request_id = str(body.get("request_id") or "")
    if not request_id:
        raise TypeError("ResidualArtifactSpec must expose request_id")
    body["source_ontology"] = "omega_capability_os_t.github_memory_evolution.ResidualArtifactSpec"
    body["bridge_boundary"] = GITHUB_MEMORY_R07_BOUNDARY
    provenance = tuple(str(item) for item in body.get("required_provenance", ()))
    return Envelope(
        graph="work",
        object_type="residual_artifact_spec",
        object_id=request_id,
        payload=body,
        provenance=provenance,
        authority="draft",
        oak_state="UNKNOWN",
    )


def adapt_reuse_outcome(receipt: Any, *, uncertainty: float = 0.0) -> Envelope:
    """Map #447 R0.5 evidence-bearing reuse outcome into Experiment.

    M+/M-/M? and utility are preserved as observed policy evidence. They are not
    converted into causal proof or scientific truth.
    """
    body = _payload(receipt)
    receipt_id = str(body.get("receipt_id") or "")
    evidence_refs = tuple(str(item) for item in body.get("evidence_refs", ()))
    if not receipt_id or not evidence_refs:
        raise TypeError("ReuseOutcomeReceipt requires receipt_id and evidence_refs")
    memory_class = getattr(receipt, "memory_class", body.get("memory_class", ""))
    utility = getattr(receipt, "utility", body.get("utility"))
    body["memory_class"] = memory_class
    body["utility"] = utility
    body["source_ontology"] = "omega_capability_os_t.github_memory_evolution.ReuseOutcomeReceipt"
    body["bridge_boundary"] = (
        "reuse_outcome != causal_proof; merge_state != M+; historical_utility != current_OAK"
    )
    return Envelope(
        graph="experiment",
        object_type="reuse_outcome_receipt",
        object_id=receipt_id,
        payload=body,
        provenance=evidence_refs,
        uncertainty=uncertainty,
        authority="read",
        oak_state="UNKNOWN",
    )


def adapt_supersession_report(report: Mapping[str, Any]) -> Envelope:
    """Map the R0.3 review-only supersession report into Provenance."""
    body = dict(report)
    fingerprint = str(body.get("fingerprint") or stable_digest(body))
    body["source_ontology"] = "omega_capability_os_t.github_memory_evolution.TemporalSupersessionMiner"
    body["bridge_boundary"] = "inferred_supersession != strong_lineage"
    return Envelope(
        graph="provenance",
        object_type="supersession_candidate_report",
        object_id=fingerprint,
        payload=body,
        provenance=("PR#447:R0.3",),
        authority="read",
        oak_state="HOLD",
    )


def adapt_llmt_federation(federation: Mapping[str, Any]) -> Envelope:
    """Map the R0.7 federation receipt into Work while preserving authority ceiling."""
    body = dict(federation)
    fingerprint = str(body.get("fingerprint") or stable_digest(body))
    body["source_ontology"] = "omega_capability_os_t.github_memory_evolution.LLMTFederationCompiler"
    body["bridge_boundary"] = (
        "LLMT_packet_count != independent_evidence; logical_identity != independent_mind"
    )
    return Envelope(
        graph="work",
        object_type="llmt_federation",
        object_id=fingerprint,
        payload=body,
        provenance=("PR#447:R0.7",),
        authority="draft",
        oak_state="UNKNOWN",
    )


def adapt_pr_llmt_inspection_plan(plan: Mapping[str, Any]) -> Envelope:
    """Map #450's exact-head inspection allocation into the Work graph."""
    body = _require_schema(
        plan,
        "omega-pr-llmt-inspection-plan/v0.1.0",
        "PR LLMT inspection plan",
    )
    body["source_ontology"] = "omega_capability_os_t.github_pr_llmt_inspection.compile_inspection_plan"
    body["bridge_boundary"] = PR_LLMT_R01_BOUNDARY
    provenance = tuple(
        item
        for item in (
            f"portfolio:{body.get('portfolio_fingerprint')}" if body.get("portfolio_fingerprint") else "",
            f"checkpoint:{body.get('checkpoint_fingerprint')}" if body.get("checkpoint_fingerprint") else "",
        )
        if item
    )
    return Envelope(
        graph="work",
        object_type="pr_llmt_inspection_plan",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=provenance,
        authority="read",
        oak_state="UNKNOWN",
    )


def adapt_pr_llmt_inspection_overlay(overlay: Mapping[str, Any]) -> Envelope:
    """Map successful/failed exact-head hydration observations into Experiment."""
    body = _require_schema(
        overlay,
        "omega-pr-llmt-inspection-overlay/v0.1.0",
        "PR LLMT inspection overlay",
    )
    body["source_ontology"] = "omega_capability_os_t.github_pr_llmt_inspection.inspect_portfolio"
    body["bridge_boundary"] = PR_LLMT_R01_BOUNDARY
    provenance = tuple(
        item
        for item in (
            f"portfolio:{body.get('portfolio_fingerprint')}" if body.get("portfolio_fingerprint") else "",
            f"plan:{body.get('plan_fingerprint')}" if body.get("plan_fingerprint") else "",
        )
        if item
    )
    return Envelope(
        graph="experiment",
        object_type="pr_llmt_inspection_overlay",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=provenance,
        authority="read",
        oak_state="HOLD",
    )


def adapt_pr_llmt_findings(findings: Mapping[str, Any]) -> Envelope:
    """Map evidence-bound PR findings into Work without promoting priority to quality."""
    body = _require_schema(
        findings,
        "omega-pr-llmt-findings/v0.2.0",
        "PR LLMT findings",
    )
    body["source_ontology"] = "omega_capability_os_t.github_pr_llmt_findings.compile_pr_findings"
    body["bridge_boundary"] = (
        PR_LLMT_R01_BOUNDARY
        + "; finding_priority != quality_score; finding != mutation_authority"
    )
    provenance = tuple(
        item
        for item in (
            f"portfolio:{body.get('portfolio_fingerprint')}" if body.get("portfolio_fingerprint") else "",
            f"filegraph:{body.get('filegraph_fingerprint')}" if body.get("filegraph_fingerprint") else "",
            f"inspection:{body.get('inspection_overlay_fingerprint')}" if body.get("inspection_overlay_fingerprint") else "",
        )
        if item
    )
    return Envelope(
        graph="work",
        object_type="pr_llmt_findings",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=provenance,
        authority="read",
        oak_state="HOLD",
    )


def issue_pr_llmt_inspection_receipt(
    plan: Mapping[str, Any],
    overlay: Mapping[str, Any],
    findings: Mapping[str, Any],
):
    """Issue a proof-carrying structural receipt for one PR-LLMT inspection wave.

    PASS certifies only declared structural invariants: fingerprint alignment,
    authority ceiling, error-free hydration, and agreement between projected and
    observed packet coverage. It does not certify semantic relevance, reusable
    behavior, optimization value, or external truth.
    """
    plan_env = adapt_pr_llmt_inspection_plan(plan)
    overlay_env = adapt_pr_llmt_inspection_overlay(overlay)
    findings_env = adapt_pr_llmt_findings(findings)

    portfolio_fingerprint = str(plan.get("portfolio_fingerprint") or "")
    alignment_ok = bool(portfolio_fingerprint) and all(
        str(item.get("portfolio_fingerprint") or "") == portfolio_fingerprint
        for item in (overlay, findings)
    )
    authority_ok = (
        overlay.get("authority", {}).get("write_authority_granted") is False
        and overlay.get("authority", {}).get("merge_authority_granted") is False
        and findings.get("authority", {}).get("write_authority_granted") is False
        and findings.get("authority", {}).get("merge_authority_granted") is False
    )
    error_free = int(overlay.get("error_count", 0)) == 0
    projected = int(plan.get("projected_packet_coverage_after_selection_count", -1))
    observed = int(overlay.get("packet_coverage_after_successful_hydration", -2))
    coverage_matches = projected >= 0 and projected == observed
    overlay_link_ok = (
        str(findings.get("inspection_overlay_fingerprint") or "")
        == str(overlay.get("fingerprint") or "")
    )

    invariants = (
        InvariantCheck(
            name="portfolio_fingerprint_alignment",
            status="PASS" if alignment_ok else "FAIL",
            detail="plan, overlay and findings share one portfolio fingerprint",
        ),
        InvariantCheck(
            name="read_only_authority_ceiling",
            status="PASS" if authority_ok else "FAIL",
            detail="no write or merge authority is granted by inspection artifacts",
        ),
        InvariantCheck(
            name="exact_hydration_error_free",
            status="PASS" if error_free else "FAIL",
            detail=f"overlay error_count={overlay.get('error_count', 0)}",
        ),
        InvariantCheck(
            name="projected_coverage_matches_observed",
            status="PASS" if coverage_matches else "FAIL",
            detail=f"projected={projected}; observed={observed}",
        ),
        InvariantCheck(
            name="findings_bind_exact_overlay",
            status="PASS" if overlay_link_ok else "FAIL",
            detail="findings inspection_overlay_fingerprint matches the observed overlay",
        ),
    )
    oak_state = "PASS" if all(item.status == "PASS" for item in invariants) else "HOLD"
    residuals = [
        "static_AST != runtime_behavior",
        "inspection_coverage != semantic_relevance",
        "candidate_rank != compatibility",
        "structural_OAK_PASS != external_truth",
    ]
    remaining = int(plan.get("remaining_uncovered_packet_count_after_selection", 0))
    if remaining > 0:
        residuals.append(f"remaining_uncovered_packets={remaining}")

    return issue_receipt(
        operator="PR_LLMT_EXACT_INSPECTION",
        inputs=(plan_env.ref,),
        outputs=(overlay_env.ref, findings_env.ref),
        assumptions=(
            "candidate head SHA is the freshness boundary for exact inspection",
            "coverage is an allocation metric, not a semantic utility metric",
        ),
        invariants=invariants,
        evidence_refs=(overlay_env.ref,),
        residuals=tuple(residuals),
        uncertainty=0.0,
        cost=float(plan.get("selected_ref_count", 0)),
        authority="read",
        risk=0.0,
        rollback="discard derived read-only inspection artifacts",
        provenance=(
            "PR#448:Universal Research ABI",
            "PR#450:PR LLMT inspection",
            f"plan:{plan_env.object_id}",
            f"overlay:{overlay_env.object_id}",
            f"findings:{findings_env.object_id}",
        ),
        oak_state=oak_state,
    )


def compile_pr_llmt_measurement_requests(findings: Mapping[str, Any]) -> dict[str, Any]:
    """Compile findings into deterministic evidence-seeking work requests.

    This bridge intentionally refuses to invent quantitative OpportunityEngine or
    Value-of-Computation inputs. Those values remain missing until an explicit
    measurement/model supplies them. The packet therefore routes future work
    toward #445/#449 contracts without importing sibling-branch implementations.
    """
    body = _require_schema(
        findings,
        "omega-pr-llmt-findings/v0.2.0",
        "PR LLMT findings",
    )
    source_fingerprint = str(body["fingerprint"])
    requests: list[dict[str, Any]] = []
    by_kind: dict[str, int] = {}

    for packet in body.get("packets", []):
        target_ref = str(packet.get("target_ref") or "")
        target_head_sha = str(packet.get("head_sha") or "")
        target_number = packet.get("target_number")
        if not target_ref or not target_head_sha:
            continue
        for finding in packet.get("findings", []):
            finding_type = str(finding.get("finding_type") or "UNKNOWN")
            measurement_kind = PR_LLMT_MEASUREMENT_KIND_BY_FINDING.get(
                finding_type,
                "manual_evidence_review",
            )
            evidence = [str(item) for item in finding.get("evidence", []) if str(item)]
            seed = {
                "source_findings_fingerprint": source_fingerprint,
                "target_ref": target_ref,
                "target_head_sha": target_head_sha,
                "finding_type": finding_type,
                "measurement_kind": measurement_kind,
                "evidence": evidence,
            }
            request_id = f"measurement:{stable_digest(seed)[:20]}"
            request = {
                "request_id": request_id,
                "target_ref": target_ref,
                "target_number": target_number,
                "target_head_sha": target_head_sha,
                "finding_type": finding_type,
                "measurement_kind": measurement_kind,
                "triage_priority": int(finding.get("priority", 0)),
                "priority_is_quality_score": False,
                "requested_action": str(finding.get("action") or ""),
                "evidence": evidence,
                "evidence_fingerprint": stable_digest(evidence),
                "finding_boundary": str(finding.get("boundary") or ""),
                "quantitative_inputs": {
                    "status": "required-before-voc-or-optimization-scoring",
                    "expected_information_gain_proxy": None,
                    "expected_cost": None,
                    "expected_risk": None,
                    "uncertainty": None,
                    "expected_savings_prior": None,
                    "confidence_debt": None,
                    "engineering_effort_hours": None,
                    "benchmark_cost": None,
                },
                "downstream_contracts": {
                    "compute_physics_pr445": {
                        "mode": "snapshot_adapter",
                        "contract": "OpportunityEvidence",
                        "quantitative_scoring_ready": False,
                    },
                    "research_self_model_pr449": {
                        "mode": "snapshot_adapter",
                        "contract": "value_of_computation",
                        "quantitative_scoring_ready": False,
                    },
                },
                "authority": {
                    "read": True,
                    "draft_analysis": True,
                    "write_authority_granted": False,
                    "merge_authority_granted": False,
                },
                "boundary": (
                    "measurement_request != measurement; triage_priority != value; "
                    "routing_contract != imported_sibling_implementation; request != mutation_authority"
                ),
            }
            requests.append(request)
            by_kind[measurement_kind] = by_kind.get(measurement_kind, 0) + 1

    requests.sort(
        key=lambda row: (
            row["target_number"] if row["target_number"] is not None else 10**9,
            -row["triage_priority"],
            row["measurement_kind"],
            row["request_id"],
        )
    )
    request_ids = [row["request_id"] for row in requests]
    payload: dict[str, Any] = {
        "schema": "omega-pr-llmt-measurement-requests/v0.1.0",
        "source_findings_fingerprint": source_fingerprint,
        "portfolio_fingerprint": body.get("portfolio_fingerprint"),
        "request_count": len(requests),
        "target_count": len({row["target_ref"] for row in requests}),
        "measurement_kind_counts": dict(sorted(by_kind.items())),
        "requests": requests,
        "authority": {
            "read": True,
            "draft_analysis": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "downstream_policy": {
            "import_pr445_implementation": False,
            "import_pr449_implementation": False,
            "numeric_opportunity_or_voc_scores_emitted": False,
            "required_next_step": "measure declared quantitative inputs before scoring",
        },
        "oak_boundaries": [
            "MEASUREMENT_REQUEST != MEASUREMENT",
            "TRIAGE_PRIORITY != VALUE",
            "UNMEASURED_INPUT != ZERO",
            "ROUTING_CONTRACT != IMPORTED_IMPLEMENTATION",
            "REQUEST != MUTATION_AUTHORITY",
        ],
    }
    if len(request_ids) != len(set(request_ids)):
        raise ValueError("measurement request ids must be unique")
    payload["fingerprint"] = stable_digest(payload)
    return payload


def adapt_pr_llmt_measurement_requests(requests: Mapping[str, Any]) -> Envelope:
    """Expose the request portfolio through the existing Research ABI Work graph."""
    body = _require_schema(
        requests,
        "omega-pr-llmt-measurement-requests/v0.1.0",
        "PR LLMT measurement requests",
    )
    body["source_ontology"] = "omega_research_abi_t.github_memory_bridge.compile_pr_llmt_measurement_requests"
    body["bridge_boundary"] = (
        "measurement_request != measurement; request_portfolio != optimization_or_VoC_result"
    )
    return Envelope(
        graph="work",
        object_type="pr_llmt_measurement_requests",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=(f"findings:{body.get('source_findings_fingerprint')}",),
        authority="read",
        oak_state="HOLD",
    )


def issue_pr_llmt_measurement_request_receipt(
    findings: Mapping[str, Any],
    requests: Mapping[str, Any],
):
    """Issue structural proof that findings were converted without false scoring."""
    findings_env = adapt_pr_llmt_findings(findings)
    requests_env = adapt_pr_llmt_measurement_requests(requests)
    rows = list(requests.get("requests", []))
    ids = [str(row.get("request_id") or "") for row in rows]
    source_ok = (
        str(requests.get("source_findings_fingerprint") or "")
        == str(findings.get("fingerprint") or "")
    )
    authority_ok = (
        requests.get("authority", {}).get("write_authority_granted") is False
        and requests.get("authority", {}).get("merge_authority_granted") is False
        and all(
            row.get("authority", {}).get("write_authority_granted") is False
            and row.get("authority", {}).get("merge_authority_granted") is False
            for row in rows
        )
    )
    unique_ok = bool(rows) and len(ids) == len(set(ids)) and all(ids)
    evidence_ok = all(bool(row.get("evidence")) for row in rows)
    unscored_ok = all(
        row.get("quantitative_inputs", {}).get("status")
        == "required-before-voc-or-optimization-scoring"
        and all(
            value is None
            for key, value in row.get("quantitative_inputs", {}).items()
            if key != "status"
        )
        and row.get("downstream_contracts", {})
        .get("compute_physics_pr445", {})
        .get("quantitative_scoring_ready") is False
        and row.get("downstream_contracts", {})
        .get("research_self_model_pr449", {})
        .get("quantitative_scoring_ready") is False
        for row in rows
    )
    invariants = (
        InvariantCheck(
            "findings_fingerprint_alignment",
            "PASS" if source_ok else "FAIL",
            "request portfolio binds the exact findings fingerprint",
        ),
        InvariantCheck(
            "read_only_authority_ceiling",
            "PASS" if authority_ok else "FAIL",
            "no request grants write or merge authority",
        ),
        InvariantCheck(
            "deterministic_unique_request_ids",
            "PASS" if unique_ok else "FAIL",
            f"request_count={len(rows)}; unique_ids={len(set(ids))}",
        ),
        InvariantCheck(
            "evidence_preserved_per_request",
            "PASS" if evidence_ok else "FAIL",
            "each emitted request carries source finding evidence",
        ),
        InvariantCheck(
            "no_unmeasured_quantitative_scoring",
            "PASS" if unscored_ok else "FAIL",
            "#445/#449 quantitative inputs remain missing until measurement",
        ),
    )
    oak_state = "PASS" if all(item.status == "PASS" for item in invariants) else "HOLD"
    return issue_receipt(
        operator="PR_FINDINGS_TO_MEASUREMENT_REQUESTS",
        inputs=(findings_env.ref,),
        outputs=(requests_env.ref,),
        assumptions=(
            "finding evidence is sufficient to request a measurement, not to infer its outcome",
            "sibling #445/#449 contracts are referenced declaratively and remain independently versioned",
        ),
        invariants=invariants,
        evidence_refs=(findings_env.ref,),
        residuals=(
            "measurement_request != measurement",
            "triage_priority != value",
            "unmeasured_quantitative_input != zero",
            "routing_contract != imported_sibling_implementation",
        ),
        uncertainty=0.0,
        cost=0.0,
        authority="read",
        risk=0.0,
        rollback="discard derived read-only measurement request portfolio",
        provenance=(
            "PR#448:Universal Research ABI",
            "PR#450:PR LLMT findings",
            "PR#445:OpportunityEvidence contract reference only",
            "PR#449:Value-of-Computation contract reference only",
            f"findings:{findings_env.object_id}",
            f"requests:{requests_env.object_id}",
        ),
        oak_state=oak_state,
    )
