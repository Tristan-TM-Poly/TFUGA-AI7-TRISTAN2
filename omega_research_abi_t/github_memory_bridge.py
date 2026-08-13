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
