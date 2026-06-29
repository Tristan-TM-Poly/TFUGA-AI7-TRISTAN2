"""ClaimGraph OAK++ for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .claim_graph import ClaimGraph, ClaimNode


@dataclass(frozen=True)
class ClaimOAKPlusNode:
    claim_id: str
    claim: str
    evidence: Tuple[str, ...]
    counterclaims: Tuple[str, ...]
    falsification_tests: Tuple[str, ...]
    confidence_status: str
    next_action: str


@dataclass(frozen=True)
class ClaimOAKPlusGraph:
    claims: Tuple[ClaimOAKPlusNode, ...]
    next_action: str


def expand_claim_oak_plus_node(node: ClaimNode) -> ClaimOAKPlusNode:
    counterclaims = (
        f"The claim may not hold outside atom {node.atom_id}.",
        "Evidence may be incomplete or domain-limited.",
    )
    tests = tuple(node.tests) + (
        "compare_against_counterexample",
        "document_assumptions_and_limits",
    )
    status = "test_seed" if node.status in {"prototype", "exploratory"} else "needs_oak_status"
    return ClaimOAKPlusNode(
        claim_id=node.claim_id,
        claim=node.claim,
        evidence=tuple(node.evidence),
        counterclaims=counterclaims,
        falsification_tests=tests,
        confidence_status=status,
        next_action="compile_claim_to_test_packet",
    )


def build_claim_oak_plus(graph: ClaimGraph | Iterable[ClaimNode]) -> ClaimOAKPlusGraph:
    nodes = graph.claims if isinstance(graph, ClaimGraph) else tuple(graph)
    return ClaimOAKPlusGraph(
        claims=tuple(expand_claim_oak_plus_node(node) for node in nodes),
        next_action="route_claim_tests_to_method_reproduction_packets",
    )
