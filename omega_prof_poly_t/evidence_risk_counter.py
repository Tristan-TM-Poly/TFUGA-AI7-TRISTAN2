"""Evidence and risk counter for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .claim_oak_plus import ClaimOAKPlusGraph, ClaimOAKPlusNode
from .method_reproduction_packet import MethodReproductionSet, MethodReproductionPacket


@dataclass(frozen=True)
class EvidenceRiskCount:
    evidence_count: int
    risk_count: int
    claim_count: int
    method_count: int
    blocked_count: int
    next_action: str


def count_evidence_risk(
    claims: ClaimOAKPlusGraph | Iterable[ClaimOAKPlusNode],
    methods: MethodReproductionSet | Iterable[MethodReproductionPacket],
    blocked_count: int = 0,
) -> EvidenceRiskCount:
    claim_nodes = claims.claims if isinstance(claims, ClaimOAKPlusGraph) else tuple(claims)
    method_nodes = methods.packets if isinstance(methods, MethodReproductionSet) else tuple(methods)
    evidence = sum(len(node.evidence) for node in claim_nodes) + sum(len(node.tests) for node in method_nodes)
    risks = sum(len(node.counterclaims) for node in claim_nodes) + sum(len(node.failure_modes) for node in method_nodes) + blocked_count
    return EvidenceRiskCount(
        evidence_count=evidence,
        risk_count=risks,
        claim_count=len(claim_nodes),
        method_count=len(method_nodes),
        blocked_count=blocked_count,
        next_action="route_counts_to_oak_manifest_plus",
    )


def render_evidence_risk_count(count: EvidenceRiskCount) -> str:
    return (
        "# Evidence Risk Count\n\n"
        f"- evidence: {count.evidence_count}\n"
        f"- risks: {count.risk_count}\n"
        f"- claims: {count.claim_count}\n"
        f"- methods: {count.method_count}\n"
        f"- blocked: {count.blocked_count}\n"
    )
