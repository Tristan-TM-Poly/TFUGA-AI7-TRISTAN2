"""Conservative method-transfer graph construction."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from .models import MethodCard, ProblemLead, TransferEdge


@dataclass(frozen=True)
class TransferCandidate:
    source_problem_id: str
    target_problem_id: str
    method_id: str
    compatibility_score: float
    shared_domains: tuple[str, ...]
    reasons: tuple[str, ...]


def compatibility(lead: ProblemLead, method: MethodCard) -> tuple[float, tuple[str, ...]]:
    shared = tuple(sorted(set(lead.domains) & set(method.domains)))
    domain_score = len(shared) / max(1, len(set(lead.domains) | set(method.domains)))
    named_bonus = 0.25 if method.method_id in lead.methods else 0.0
    return min(1.0, round(domain_score + named_bonus, 6)), shared


def candidate_transfers(
    leads: Iterable[ProblemLead],
    methods: Iterable[MethodCard],
    threshold: float = 0.15,
    max_pairs_per_method: int = 5000,
) -> tuple[TransferCandidate, ...]:
    materialized_leads = tuple(sorted(leads, key=lambda item: item.lead_id))
    findings: list[TransferCandidate] = []
    for method in sorted(methods, key=lambda item: item.method_id):
        compatible: list[tuple[ProblemLead, float, tuple[str, ...]]] = []
        for lead in materialized_leads:
            score, shared = compatibility(lead, method)
            if score >= threshold:
                compatible.append((lead, score, shared))
        pair_count = 0
        for left, right in combinations(compatible, 2):
            if pair_count >= max_pairs_per_method:
                break
            left_lead, left_score, left_shared = left
            right_lead, right_score, right_shared = right
            shared = tuple(sorted(set(left_shared) & set(right_shared)))
            score = round(min(left_score, right_score), 6)
            findings.append(
                TransferCandidate(
                    source_problem_id=left_lead.lead_id,
                    target_problem_id=right_lead.lead_id,
                    method_id=method.method_id,
                    compatibility_score=score,
                    shared_domains=shared,
                    reasons=(
                        "shared declared mathematical domains",
                        "method transfer remains a hypothesis until round-trip checks pass",
                    ),
                )
            )
            pair_count += 1
    return tuple(findings)


def compile_transfer_edges(
    candidates: Iterable[TransferCandidate],
) -> tuple[TransferEdge, ...]:
    edges: list[TransferEdge] = []
    for ordinal, candidate in enumerate(candidates):
        edges.append(
            TransferEdge(
                edge_id=f"OPA-TRANSFER-{ordinal:08d}",
                source_problem_id=candidate.source_problem_id,
                target_problem_id=candidate.target_problem_id,
                method_id=candidate.method_id,
                forward_hypothesis=(
                    f"Test whether {candidate.method_id} transports a useful invariant from "
                    f"{candidate.source_problem_id} to {candidate.target_problem_id}"
                ),
                reverse_check=(
                    f"Attempt reconstruction or contradiction from {candidate.target_problem_id} "
                    f"back to {candidate.source_problem_id}"
                ),
                shared_invariants=candidate.shared_domains,
                round_trip_required=True,
                transfer_validated=False,
            )
        )
    return tuple(edges)


def transfer_summary(edges: Iterable[TransferEdge]) -> dict[str, object]:
    materialized = tuple(edges)
    return {
        "edge_count": len(materialized),
        "validated_count": sum(edge.transfer_validated for edge in materialized),
        "round_trip_required_count": sum(edge.round_trip_required for edge in materialized),
        "transfer_is_hypothesis_until_validated": True,
    }
