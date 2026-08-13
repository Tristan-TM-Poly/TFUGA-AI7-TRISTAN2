from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from .core import Envelope, stable_digest

GITHUB_MEMORY_R07_BOUNDARY = (
    "native_structure_bridge != semantic_equivalence_or_causal_validation"
)


def _payload(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("bridge value must be a dataclass or mapping")


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
