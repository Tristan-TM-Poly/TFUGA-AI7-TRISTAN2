"""Deterministic software benchmark fixtures."""
from __future__ import annotations

from dataclasses import asdict

from .adversary import boundary_cases, search_counterexamples
from .graph import ProofGraph
from .models import Claim, ClaimKind, EdgeKind, OAKLevel, ProblemId, ProofEdge
from .registry import validate_registry


def poincare_dependency_fixture() -> ProofGraph:
    graph = ProofGraph(ProblemId.POINCARE)
    claims = (
        Claim("closed-simply-connected-3m", ProblemId.POINCARE, ClaimKind.DEFINITION, "M is a closed simply connected 3-manifold", oak_level=OAKLevel.WELL_TYPED),
        Claim("ricci-flow-framework", ProblemId.POINCARE, ClaimKind.KNOWN_THEOREM, "Ricci flow framework is available for the fixture", oak_level=OAKLevel.KNOWN_CASES),
        Claim("noncollapsing-control", ProblemId.POINCARE, ClaimKind.LEMMA, "Non-collapsing control holds in the fixture", oak_level=OAKLevel.RESTRICTED_PROOF),
        Claim("surgery-control", ProblemId.POINCARE, ClaimKind.LEMMA, "Surgery is controlled in the fixture", oak_level=OAKLevel.RESTRICTED_PROOF),
        Claim("geometrization-conclusion", ProblemId.POINCARE, ClaimKind.KNOWN_THEOREM, "The fixture reaches the geometrization conclusion", oak_level=OAKLevel.RESTRICTED_PROOF),
        Claim("poincare-conclusion", ProblemId.POINCARE, ClaimKind.KNOWN_THEOREM, "M is homeomorphic to S^3", oak_level=OAKLevel.RESTRICTED_PROOF),
    )
    for claim in claims:
        graph.add_claim(claim)
    edges = (
        ProofEdge("e-noncollapse", ProblemId.POINCARE, ("ricci-flow-framework",), "noncollapsing-control", EdgeKind.IMPLIES, oak_level=OAKLevel.RESTRICTED_PROOF),
        ProofEdge("e-surgery", ProblemId.POINCARE, ("ricci-flow-framework", "noncollapsing-control"), "surgery-control", EdgeKind.IMPLIES, oak_level=OAKLevel.RESTRICTED_PROOF),
        ProofEdge("e-geo", ProblemId.POINCARE, ("surgery-control",), "geometrization-conclusion", EdgeKind.IMPLIES, oak_level=OAKLevel.RESTRICTED_PROOF),
        ProofEdge("e-poincare", ProblemId.POINCARE, ("closed-simply-connected-3m", "geometrization-conclusion"), "poincare-conclusion", EdgeKind.IMPLIES, oak_level=OAKLevel.RESTRICTED_PROOF),
    )
    for edge in edges:
        graph.add_edge(edge)
    return graph


def run_benchmark() -> dict[str, object]:
    registry_errors = validate_registry()
    graph = poincare_dependency_fixture()
    graph_report = graph.validate()
    seeds = ("closed-simply-connected-3m", "ricci-flow-framework")
    reached = graph.reachable_claims(seeds, minimum_level=OAKLevel.RESTRICTED_PROOF)
    frontier_without_noncollapse = graph.minimal_frontier(
        "poincare-conclusion",
        ("closed-simply-connected-3m", "ricci-flow-framework", "surgery-control"),
        minimum_level=OAKLevel.RESTRICTED_PROOF,
    )

    finite_cases = boundary_cases({"x": (-2, -1, 0, 1, 2), "y": (-2, 0, 2)})
    counterexamples = search_counterexamples(
        claim_id="toy-square-nonnegative",
        predicate=lambda case: case["x"] ** 2 + case["y"] ** 2 >= 0,
        cases=finite_cases,
    )
    return {
        "schema": "omega-millennium-benchmark/1",
        "registry_valid": not registry_errors,
        "registry_errors": registry_errors,
        "graph_valid": graph_report.valid,
        "graph_metrics": dict(graph_report.metrics),
        "poincare_fixture_reaches_conclusion": "poincare-conclusion" in reached,
        "reachable_claims": sorted(reached),
        "local_frontier_fixture": frontier_without_noncollapse,
        "toy_counterexamples": [asdict(item) for item in counterexamples],
        "finite_test_is_not_proof": True,
        "solution_claimed": False,
        "status": "CERTIFIED_SOFTWARE_FIXTURE_R0_1" if not registry_errors and graph_report.valid and "poincare-conclusion" in reached else "FAILED",
    }
