"""Semantic hardening overrides for R0.6 claim assessment."""
from __future__ import annotations

from typing import Mapping, Sequence

from .model import EvidenceEdge, EvidenceNode, PROMOTION_RANK, stable_digest

SUPPORT_RELATIONS = {"supports", "proves_restricted_case", "improves_bound", "reproduces"}


def assess_claims_hardened(
    nodes: Mapping[str, EvidenceNode],
    edges: Sequence[EvidenceEdge],
) -> list[dict]:
    """Assess claims while treating `violates` as a blocker, never a discharge."""
    incoming: dict[str, list[EvidenceEdge]] = {node_id: [] for node_id in nodes}
    outgoing: dict[str, list[EvidenceEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        incoming[edge.target_node_id].append(edge)
        outgoing[edge.source_node_id].append(edge)

    discharged = {edge.target_node_id for edge in edges if edge.relation == "discharges"}
    violated = {edge.target_node_id for edge in edges if edge.relation == "violates"}
    assessments: list[dict] = []
    for claim in sorted(
        (node for node in nodes.values() if node.node_type == "claim"),
        key=lambda item: item.node_id,
    ):
        requested = str(claim.metadata.get("requested_status", "candidate"))
        achieved = "candidate"
        blockers: list[str] = []
        support_ids: list[str] = []
        contradiction_ids: list[str] = []
        numerical_support = False
        exact_certificate = False
        restricted_formal = False
        general_formal_candidate = False
        kernel_checked_general = False
        accepted_review = False

        dependencies = [
            edge.target_node_id
            for edge in outgoing[claim.node_id]
            if edge.relation == "depends_on"
        ]
        for assumption_id in dependencies:
            if assumption_id in violated:
                blockers.append(f"violated_assumption:{assumption_id}")
            elif assumption_id not in discharged:
                blockers.append(f"undischarged_assumption:{assumption_id}")

        scoped_barriers = [
            edge.source_node_id
            for edge in incoming[claim.node_id]
            if edge.relation == "scopes"
            and nodes[edge.source_node_id].node_type == "barrier"
        ]
        for barrier_id in scoped_barriers:
            if barrier_id in violated:
                blockers.append(f"violated_barrier:{barrier_id}")
            elif barrier_id not in discharged:
                blockers.append(f"active_barrier:{barrier_id}")

        for edge in incoming[claim.node_id]:
            source = nodes[edge.source_node_id]
            if edge.relation == "contradicts":
                contradiction_ids.append(source.node_id)
                blockers.append(f"contradiction:{source.node_id}")
                continue
            if edge.relation not in SUPPORT_RELATIONS:
                continue
            support_ids.append(source.node_id)
            if source.node_type == "evidence":
                kind = str(source.metadata.get("evidence_kind", ""))
                if kind in {"numerical", "symbolic", "experiment", "literature", "proof_text"}:
                    numerical_support = numerical_support or kind in {"numerical", "symbolic", "experiment"}
                    achieved = max((achieved, "experimental"), key=PROMOTION_RANK.get)
                if kind == "exact_computation" and source.metadata.get("certificate_verified") is True:
                    exact_certificate = True
                    achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)
            elif source.node_type == "computation_receipt":
                achieved = max((achieved, "experimental"), key=PROMOTION_RANK.get)
                if source.metadata.get("certificate_verified") is True:
                    exact_certificate = True
                    achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)
            elif source.node_type == "formal_artifact":
                scope = str(source.metadata.get("proof_scope", ""))
                checked = source.metadata.get("kernel_checked") is True
                if scope == "restricted" and checked:
                    restricted_formal = True
                    achieved = max((achieved, "formal_restricted"), key=PROMOTION_RANK.get)
                elif scope == "general" and checked:
                    kernel_checked_general = True
                    achieved = max((achieved, "kernel_checked_general"), key=PROMOTION_RANK.get)
                elif scope == "general":
                    general_formal_candidate = True
                    achieved = max((achieved, "general_proof_candidate"), key=PROMOTION_RANK.get)
            elif source.node_type == "independent_review":
                outcome = str(source.metadata.get("outcome", ""))
                if outcome == "accepted":
                    accepted_review = True
                elif outcome in {"challenged", "rejected"}:
                    blockers.append(f"review_{outcome}:{source.node_id}")

        if kernel_checked_general and accepted_review:
            achieved = "independently_reviewed_general"
        elif restricted_formal:
            achieved = max((achieved, "formal_restricted"), key=PROMOTION_RANK.get)
        elif exact_certificate:
            achieved = max((achieved, "restricted_result"), key=PROMOTION_RANK.get)

        if PROMOTION_RANK[requested] >= PROMOTION_RANK["general_proof_candidate"]:
            if not (general_formal_candidate or kernel_checked_general):
                blockers.append("general_status_requires_general_formal_artifact")
            if numerical_support and not (general_formal_candidate or kernel_checked_general):
                blockers.append("general_proof_from_numerical_evidence_forbidden")
        if PROMOTION_RANK[achieved] < PROMOTION_RANK[requested]:
            blockers.append(f"insufficient_evidence:{achieved}<{requested}")

        blockers = sorted(set(blockers))
        row = {
            "claim_id": claim.node_id,
            "canonical_problem_id": claim.canonical_problem_id,
            "requested_status": requested,
            "achieved_status": achieved,
            "promotion_allowed": not blockers and PROMOTION_RANK[achieved] >= PROMOTION_RANK[requested],
            "support_node_ids": sorted(set(support_ids)),
            "contradiction_node_ids": sorted(set(contradiction_ids)),
            "dependency_assumption_ids": sorted(set(dependencies)),
            "scoped_barrier_ids": sorted(set(scoped_barriers)),
            "blockers": blockers,
            "mathematical_truth_probability_claimed": False,
            "general_proof_from_numerical_evidence": False,
        }
        row["assessment_digest"] = stable_digest(row)
        assessments.append(row)
    return assessments
