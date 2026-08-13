"""Evidence-leverage allocation for PR-LLMT measurement requests.

This module is a thin residual layer over the existing Universal Research ABI.
It answers a narrower question than Value of Computation: which *evidence
anchors* are shared by the largest number of pending measurement requests?

The allocator is deliberately structural. It does not infer information gain,
cost, risk, speedup, utility, or economic value. Raw measurement requests are
not routed into #445 OpportunityEvidence or #449 value_of_computation until
quantitative inputs are measured with provenance.
"""
from __future__ import annotations

from typing import Any, Mapping

from .core import Envelope, InvariantCheck, stable_digest
from .github_memory_bridge import adapt_pr_llmt_measurement_requests
from .receipts import issue_receipt

MEASUREMENT_ALLOCATION_SCHEMA = "omega-pr-llmt-measurement-allocation/v0.1.0"
MEASUREMENT_ALLOCATION_POLICY = "greedy_marginal_request_evidence_coverage/v0.1"

PR449_VOC_REQUIRED_FIELDS = (
    "expected_information_gain_proxy",
    "expected_cost",
    "expected_risk",
    "uncertainty",
)
PR445_OPPORTUNITY_REQUIRED_FIELDS = (
    "static_complexity",
    "graph_centrality",
    "usage_weight",
    "regression_signal",
    "expected_savings_prior",
    "confidence_debt",
    "engineering_effort_hours",
    "benchmark_cost",
)


def _require_requests(requests: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(requests)
    expected = "omega-pr-llmt-measurement-requests/v0.1.0"
    if body.get("schema") != expected:
        raise TypeError(f"PR LLMT measurement allocation requires schema {expected}")
    if not body.get("fingerprint"):
        body["fingerprint"] = stable_digest(body)
    return body


def _contract_readiness(
    rows: list[dict[str, Any]],
    required_fields: tuple[str, ...],
) -> dict[str, Any]:
    missing_counts = {field: 0 for field in required_fields}
    ready_ids: list[str] = []
    blocked_ids: list[str] = []
    provenance_missing = 0

    for row in rows:
        request_id = str(row.get("request_id") or "")
        quantitative = row.get("quantitative_inputs", {})
        missing = [field for field in required_fields if quantitative.get(field) is None]
        for field in missing:
            missing_counts[field] += 1
        provenance_ready = (
            quantitative.get("status") == "measured-with-provenance"
            and bool(row.get("quantitative_provenance"))
        )
        if not provenance_ready:
            provenance_missing += 1
        if not missing and provenance_ready:
            ready_ids.append(request_id)
        else:
            blocked_ids.append(request_id)

    return {
        "required_fields": list(required_fields),
        "ready_request_count": len(ready_ids),
        "blocked_request_count": len(blocked_ids),
        "ready_request_ids": sorted(ready_ids),
        "blocked_request_ids": sorted(blocked_ids),
        "missing_field_counts": dict(sorted(missing_counts.items())),
        "missing_measured_provenance_count": provenance_missing,
        "readiness_boundary": (
            "raw request fields or injected numbers are not sufficient; quantitative routing "
            "requires measured-with-provenance status plus explicit provenance"
        ),
    }


def _compile_anchor_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors: dict[str, dict[str, Any]] = {}
    for row in rows:
        request_id = str(row.get("request_id") or "")
        target_ref = str(row.get("target_ref") or "")
        measurement_kind = str(row.get("measurement_kind") or "")
        priority = int(row.get("triage_priority", 0))
        for evidence in dict.fromkeys(str(item) for item in row.get("evidence", []) if str(item)):
            anchor_id = f"evidence-anchor:{stable_digest(evidence)[:20]}"
            bucket = anchors.setdefault(
                anchor_id,
                {
                    "anchor_id": anchor_id,
                    "evidence_anchor": evidence,
                    "request_ids": set(),
                    "target_refs": set(),
                    "measurement_kinds": set(),
                    "triage_priorities": [],
                },
            )
            bucket["request_ids"].add(request_id)
            bucket["target_refs"].add(target_ref)
            bucket["measurement_kinds"].add(measurement_kind)
            bucket["triage_priorities"].append(priority)

    compiled: list[dict[str, Any]] = []
    for bucket in anchors.values():
        priorities = list(bucket["triage_priorities"])
        compiled.append(
            {
                "anchor_id": bucket["anchor_id"],
                "evidence_anchor": bucket["evidence_anchor"],
                "request_ids": sorted(bucket["request_ids"]),
                "target_refs": sorted(bucket["target_refs"]),
                "measurement_kinds": sorted(bucket["measurement_kinds"]),
                "request_fanout": len(bucket["request_ids"]),
                "target_fanout": len(bucket["target_refs"]),
                "max_triage_priority": max(priorities, default=0),
                "triage_priority_mass_tiebreak_only": sum(priorities),
                "boundary": (
                    "shared evidence-anchor fanout measures reuse of an evidence source, not the "
                    "probability that one measurement resolves every target-specific request"
                ),
            }
        )
    compiled.sort(
        key=lambda row: (
            -row["request_fanout"],
            -row["target_fanout"],
            -row["max_triage_priority"],
            -row["triage_priority_mass_tiebreak_only"],
            row["anchor_id"],
        )
    )
    return compiled


def compile_pr_llmt_measurement_allocation(
    requests: Mapping[str, Any],
    *,
    max_anchors: int | None = 12,
) -> dict[str, Any]:
    """Allocate evidence-acquisition attention by marginal request coverage.

    ``max_anchors`` is an operational wave budget, never an architecture hard cap.
    Passing ``None`` lets the deterministic selector continue until no remaining
    request can gain coverage from another evidence anchor.
    """
    if max_anchors is not None and max_anchors < 0:
        raise ValueError("max_anchors must be non-negative or None")

    body = _require_requests(requests)
    rows = [dict(row) for row in body.get("requests", [])]
    request_lookup = {str(row.get("request_id") or ""): row for row in rows}
    if len(request_lookup) != len(rows) or not all(request_lookup):
        raise ValueError("measurement requests require unique non-empty request_id values")

    anchors = _compile_anchor_rows(rows)
    uncovered = set(request_lookup)
    selected_ids: set[str] = set()
    selected: list[dict[str, Any]] = []
    budget = len(anchors) if max_anchors is None else min(max_anchors, len(anchors))

    for step in range(budget):
        candidates: list[tuple[tuple[Any, ...], dict[str, Any], list[str], list[str]]] = []
        for anchor in anchors:
            if anchor["anchor_id"] in selected_ids:
                continue
            marginal_ids = sorted(set(anchor["request_ids"]) & uncovered)
            if not marginal_ids:
                continue
            marginal_targets = sorted(
                {
                    str(request_lookup[request_id].get("target_ref") or "")
                    for request_id in marginal_ids
                }
            )
            key = (
                -len(marginal_ids),
                -len(marginal_targets),
                -anchor["request_fanout"],
                -anchor["target_fanout"],
                -anchor["max_triage_priority"],
                -anchor["triage_priority_mass_tiebreak_only"],
                anchor["anchor_id"],
            )
            candidates.append((key, anchor, marginal_ids, marginal_targets))
        if not candidates:
            break
        _, anchor, marginal_ids, marginal_targets = min(candidates, key=lambda item: item[0])
        selected_ids.add(anchor["anchor_id"])
        selected.append(
            {
                **anchor,
                "selection_step": step + 1,
                "marginal_request_count": len(marginal_ids),
                "marginal_request_ids": marginal_ids,
                "marginal_target_count": len(marginal_targets),
                "marginal_target_refs": marginal_targets,
            }
        )
        uncovered.difference_update(marginal_ids)

    covered_ids = sorted(set(request_lookup) - uncovered)
    covered_targets = sorted(
        {
            str(request_lookup[request_id].get("target_ref") or "")
            for request_id in covered_ids
        }
    )
    all_targets = {
        str(row.get("target_ref") or "")
        for row in rows
        if str(row.get("target_ref") or "")
    }
    request_count = len(rows)
    target_count = len(all_targets)

    readiness = {
        "pr445_opportunity_evidence": _contract_readiness(rows, PR445_OPPORTUNITY_REQUIRED_FIELDS),
        "pr449_value_of_computation": _contract_readiness(rows, PR449_VOC_REQUIRED_FIELDS),
    }
    ready_union = set(readiness["pr445_opportunity_evidence"]["ready_request_ids"]) | set(
        readiness["pr449_value_of_computation"]["ready_request_ids"]
    )

    payload: dict[str, Any] = {
        "schema": MEASUREMENT_ALLOCATION_SCHEMA,
        "source_requests_fingerprint": body.get("fingerprint"),
        "source_findings_fingerprint": body.get("source_findings_fingerprint"),
        "selection_policy": MEASUREMENT_ALLOCATION_POLICY,
        "operational_budget": {
            "max_anchors": max_anchors,
            "architecture_hard_cap": False,
        },
        "request_count": request_count,
        "target_count": target_count,
        "evidence_anchor_count": len(anchors),
        "evidence_anchors": anchors,
        "selected_anchor_count": len(selected),
        "selected_anchor_ids": [row["anchor_id"] for row in selected],
        "selected_anchors": selected,
        "projected_request_coverage_count": len(covered_ids),
        "projected_request_coverage_fraction": round(len(covered_ids) / request_count, 6) if request_count else 0.0,
        "projected_target_coverage_count": len(covered_targets),
        "projected_target_coverage_fraction": round(len(covered_targets) / target_count, 6) if target_count else 0.0,
        "remaining_uncovered_request_count": len(uncovered),
        "remaining_uncovered_request_ids": sorted(uncovered),
        "readiness": readiness,
        "quantitatively_ready_request_count": len(ready_union),
        "quantitatively_ready_request_ids": sorted(ready_union),
        "downstream_policy": {
            "numeric_opportunity_or_voc_scores_emitted": False,
            "raw_request_portfolio_is_measurement_result": False,
            "route_to_pr445_or_pr449_only_after_measured_provenance": True,
            "selected_anchor_is_execution_authority": False,
        },
        "authority": {
            "read": True,
            "draft_analysis": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "oak_boundaries": [
            "EVIDENCE_ANCHOR_FANOUT != VALUE_OF_MEASUREMENT",
            "REQUEST_COVERAGE != RESOLVED_UNCERTAINTY",
            "TRIAGE_PRIORITY_TIEBREAK != QUALITY_OR_VALUE",
            "RAW_REQUEST != MEASURED_RESULT",
            "QUANTITATIVE_READINESS_REQUIRES_PROVENANCE",
            "ALLOCATION != EXECUTION_OR_MUTATION_AUTHORITY",
        ],
    }
    payload["fingerprint"] = stable_digest(payload)
    return payload


def adapt_pr_llmt_measurement_allocation(allocation: Mapping[str, Any]) -> Envelope:
    body = dict(allocation)
    if body.get("schema") != MEASUREMENT_ALLOCATION_SCHEMA:
        raise TypeError(f"measurement allocation requires schema {MEASUREMENT_ALLOCATION_SCHEMA}")
    if not body.get("fingerprint"):
        body["fingerprint"] = stable_digest(body)
    body["source_ontology"] = "omega_research_abi_t.measurement_allocation.compile_pr_llmt_measurement_allocation"
    body["bridge_boundary"] = (
        "evidence allocation != Value of Computation; selected anchor != executed measurement"
    )
    return Envelope(
        graph="work",
        object_type="pr_llmt_measurement_allocation",
        object_id=str(body["fingerprint"]),
        payload=body,
        provenance=(f"measurement-requests:{body.get('source_requests_fingerprint')}",),
        authority="read",
        oak_state="HOLD",
    )


def issue_pr_llmt_measurement_allocation_receipt(
    requests: Mapping[str, Any],
    allocation: Mapping[str, Any],
):
    requests_env = adapt_pr_llmt_measurement_requests(requests)
    allocation_env = adapt_pr_llmt_measurement_allocation(allocation)
    request_rows = [dict(row) for row in requests.get("requests", [])]
    request_ids = {str(row.get("request_id") or "") for row in request_rows}
    selected = [dict(row) for row in allocation.get("selected_anchors", [])]
    selected_ids = [str(row.get("anchor_id") or "") for row in selected]
    covered = {
        str(request_id)
        for row in selected
        for request_id in row.get("request_ids", [])
        if str(request_id) in request_ids
    }

    source_ok = (
        str(allocation.get("source_requests_fingerprint") or "")
        == str(requests.get("fingerprint") or "")
    )
    authority_ok = (
        allocation.get("authority", {}).get("write_authority_granted") is False
        and allocation.get("authority", {}).get("merge_authority_granted") is False
    )
    selection_ok = (
        len(selected_ids) == len(set(selected_ids))
        and all(selected_ids)
        and len(selected_ids) == int(allocation.get("selected_anchor_count", -1))
    )
    coverage_ok = (
        len(covered) == int(allocation.get("projected_request_coverage_count", -1))
        and len(request_ids - covered) == int(allocation.get("remaining_uncovered_request_count", -1))
    )
    readiness_expected = {
        "pr445_opportunity_evidence": _contract_readiness(request_rows, PR445_OPPORTUNITY_REQUIRED_FIELDS),
        "pr449_value_of_computation": _contract_readiness(request_rows, PR449_VOC_REQUIRED_FIELDS),
    }
    readiness_ok = allocation.get("readiness") == readiness_expected
    no_false_scoring = (
        allocation.get("downstream_policy", {}).get("numeric_opportunity_or_voc_scores_emitted") is False
        and allocation.get("downstream_policy", {}).get("selected_anchor_is_execution_authority") is False
    )

    invariants = (
        InvariantCheck(
            "measurement_request_fingerprint_alignment",
            "PASS" if source_ok else "FAIL",
            "allocation binds the exact measurement-request portfolio fingerprint",
        ),
        InvariantCheck(
            "read_only_authority_ceiling",
            "PASS" if authority_ok else "FAIL",
            "allocation grants neither write nor merge authority",
        ),
        InvariantCheck(
            "deterministic_unique_selected_anchors",
            "PASS" if selection_ok else "FAIL",
            f"selected_anchor_count={len(selected_ids)}; unique={len(set(selected_ids))}",
        ),
        InvariantCheck(
            "projected_request_coverage_reconstructs",
            "PASS" if coverage_ok else "FAIL",
            f"covered={len(covered)}; remaining={len(request_ids - covered)}",
        ),
        InvariantCheck(
            "quantitative_readiness_is_provenance_gated",
            "PASS" if readiness_ok else "FAIL",
            "#445/#449 routing readiness is recomputed from measured-with-provenance inputs",
        ),
        InvariantCheck(
            "no_false_value_or_execution_claim",
            "PASS" if no_false_scoring else "FAIL",
            "allocation emits structural fanout only and grants no execution authority",
        ),
    )
    oak_state = "PASS" if all(item.status == "PASS" for item in invariants) else "HOLD"
    return issue_receipt(
        operator="PR_MEASUREMENT_EVIDENCE_ALLOCATION",
        inputs=(requests_env.ref,),
        outputs=(allocation_env.ref,),
        assumptions=(
            "literal shared evidence anchors can be acquired once and reused as inputs to multiple target-specific reviews",
            "fanout is an allocation heuristic and is not Value of Measurement or Value of Computation",
        ),
        invariants=invariants,
        evidence_refs=(requests_env.ref,),
        residuals=(
            "evidence_anchor_fanout != value_of_measurement",
            "request_coverage != resolved_uncertainty",
            "quantitative_inputs_remain_unmeasured",
            "allocation_plan != measurement_execution",
        ),
        uncertainty=0.0,
        cost=0.0,
        authority="read",
        risk=0.0,
        rollback="discard derived read-only measurement allocation",
        provenance=(
            "PR#448:Universal Research ABI",
            "PR#450:Measurement request portfolio",
            "PR#445:OpportunityEvidence contract reference only",
            "PR#449:Value-of-Computation contract reference only",
            f"requests:{requests_env.object_id}",
            f"allocation:{allocation_env.object_id}",
        ),
        oak_state=oak_state,
    )
