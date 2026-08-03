from __future__ import annotations

from dataclasses import replace
import json

import pytest

from omega_millennium_t import (
    Claim,
    ClaimKind,
    DirectionalImplication,
    EdgeKind,
    Evidence,
    EvidenceKind,
    GENESIS,
    OAKLevel,
    ProblemId,
    ProofEdge,
    ProofGraph,
    StrategyScore,
    adversarial_report,
    allocate_finite_budget,
    all_problems,
    audit_equivalence,
    boundary_cases,
    cartesian_cases,
    compile_campaign,
    create_receipt,
    evaluate_claim,
    export_lean_skeleton,
    get_problem,
    poincare_dependency_fixture,
    rank_strategies,
    run_benchmark,
    search_counterexamples,
    update_strategy,
    validate_registry,
    verify_chain,
)
from omega_millennium_t.models import ProblemStatus


def test_registry_has_exactly_seven_unique_problems():
    problems = all_problems()
    assert len(problems) == 7
    assert {problem.problem_id for problem in problems} == set(ProblemId)
    assert validate_registry() == ()


def test_only_poincare_is_solved_benchmark():
    solved = [problem for problem in all_problems() if problem.status == ProblemStatus.SOLVED_BENCHMARK]
    assert [problem.problem_id for problem in solved] == [ProblemId.POINCARE]
    assert solved[0].benchmark_role


@pytest.mark.parametrize("problem_id", list(ProblemId))
def test_every_problem_has_outcomes_barriers_and_shortcuts(problem_id):
    problem = get_problem(problem_id)
    assert problem.accepted_outcomes
    assert problem.barriers
    assert problem.forbidden_shortcuts
    assert problem.validate() == ()


def test_graph_rejects_cross_problem_claim():
    graph = ProofGraph(ProblemId.RIEMANN)
    with pytest.raises(ValueError, match="problem_id"):
        graph.add_claim(Claim("x", ProblemId.NAVIER_STOKES, ClaimKind.LEMMA, "x"))


def test_graph_rejects_duplicate_claims():
    graph = ProofGraph(ProblemId.RIEMANN)
    claim = Claim("x", ProblemId.RIEMANN, ClaimKind.LEMMA, "x")
    graph.add_claim(claim)
    with pytest.raises(ValueError, match="duplicate"):
        graph.add_claim(claim)


def test_graph_rejects_unknown_edge_nodes():
    graph = ProofGraph(ProblemId.RIEMANN)
    graph.add_claim(Claim("a", ProblemId.RIEMANN, ClaimKind.LEMMA, "a"))
    with pytest.raises(ValueError, match="unknown"):
        graph.add_edge(ProofEdge("e", ProblemId.RIEMANN, ("a",), "b"))


def test_hyperedge_requires_all_premises():
    graph = ProofGraph(ProblemId.RIEMANN)
    for claim_id in ("a", "b", "c"):
        graph.add_claim(Claim(claim_id, ProblemId.RIEMANN, ClaimKind.LEMMA, claim_id, oak_level=OAKLevel.RESTRICTED_PROOF))
    graph.add_edge(ProofEdge("e", ProblemId.RIEMANN, ("a", "b"), "c", oak_level=OAKLevel.RESTRICTED_PROOF))
    assert "c" not in graph.reachable_claims(("a",), minimum_level=OAKLevel.RESTRICTED_PROOF)
    assert "c" in graph.reachable_claims(("a", "b"), minimum_level=OAKLevel.RESTRICTED_PROOF)


def test_graph_minimum_level_blocks_weak_edge():
    graph = ProofGraph(ProblemId.RIEMANN)
    for claim_id in ("a", "b"):
        graph.add_claim(Claim(claim_id, ProblemId.RIEMANN, ClaimKind.LEMMA, claim_id))
    graph.add_edge(ProofEdge("e", ProblemId.RIEMANN, ("a",), "b", oak_level=OAKLevel.WELL_TYPED))
    assert "b" not in graph.reachable_claims(("a",), minimum_level=OAKLevel.RESTRICTED_PROOF)


def test_poincare_fixture_reaches_conclusion():
    graph = poincare_dependency_fixture()
    reached = graph.reachable_claims(
        ("closed-simply-connected-3m", "ricci-flow-framework"),
        minimum_level=OAKLevel.RESTRICTED_PROOF,
    )
    assert "poincare-conclusion" in reached
    assert graph.validate().valid


def test_graph_digest_is_deterministic():
    assert poincare_dependency_fixture().digest() == poincare_dependency_fixture().digest()


def test_local_frontier_returns_missing_premise_option():
    graph = ProofGraph(ProblemId.NAVIER_STOKES)
    for claim_id in ("a", "b", "target"):
        graph.add_claim(Claim(claim_id, ProblemId.NAVIER_STOKES, ClaimKind.LEMMA, claim_id, oak_level=OAKLevel.RESTRICTED_PROOF))
    graph.add_edge(ProofEdge("e", ProblemId.NAVIER_STOKES, ("a", "b"), "target", oak_level=OAKLevel.RESTRICTED_PROOF))
    assert graph.minimal_frontier("target", ("a",), minimum_level=OAKLevel.RESTRICTED_PROOF) == ("b",)


def test_cartesian_case_count_and_order():
    cases = cartesian_cases({"b": (0, 1), "a": (2, 3, 4)})
    assert len(cases) == 6
    assert list(cases[0]) == ["a", "b"]


def test_boundary_cases_are_deterministic_and_finite():
    left = boundary_cases({"x": (-2, -1, 0, 1, 2), "y": (-1, 0, 1)})
    right = boundary_cases({"y": (-1, 0, 1), "x": (-2, -1, 0, 1, 2)})
    assert left == right
    assert 1 <= len(left) <= 5


def test_counterexample_search_finds_witness():
    cases = cartesian_cases({"x": (-2, -1, 0, 1, 2)})
    records = search_counterexamples(claim_id="positive", predicate=lambda case: case["x"] > 0, cases=cases)
    assert records
    assert any(record.witness["x"] == 0 for record in records)
    assert all(record.reproducible for record in records)


def test_counterexample_exception_is_recorded():
    records = search_counterexamples(
        claim_id="division",
        predicate=lambda case: 1 / case["x"] > 0,
        cases=({"x": 0},),
    )
    assert "ZeroDivisionError" in records[0].explanation


def test_adversarial_report_never_calls_finite_survival_proof():
    report = adversarial_report(())
    assert report["claim_survived_finite_harness"] is True
    assert report["finite_harness_is_not_proof"] is True


def test_equivalence_requires_both_directions():
    one_way = (DirectionalImplication("A", "B", "fixture", OAKLevel.RESTRICTED_PROOF),)
    audit = audit_equivalence("A", "B", one_way, minimum_level=OAKLevel.RESTRICTED_PROOF)
    assert not audit.valid_equivalence
    assert "missing reverse implication" in audit.blockers


def test_equivalence_certified_at_weaker_direction():
    implications = (
        DirectionalImplication("A", "B", "forward", OAKLevel.FORMALIZED),
        DirectionalImplication("B", "A", "reverse", OAKLevel.RESTRICTED_PROOF),
    )
    audit = audit_equivalence("A", "B", implications, minimum_level=OAKLevel.RESTRICTED_PROOF)
    assert audit.valid_equivalence
    assert audit.certified_level == OAKLevel.RESTRICTED_PROOF


def test_numeric_evidence_cannot_certify_solution():
    evidence = Evidence("num", EvidenceKind.NUMERICAL, "finite scan", digest="sha256:abc")
    claim = Claim(
        "rh-solution",
        ProblemId.RIEMANN,
        ClaimKind.SOLUTION_CLAIM,
        "All zeros lie on the critical line",
        evidence_ids=("num",),
        oak_level=OAKLevel.NUMERICALLY_TESTED,
    )
    decision = evaluate_claim(claim, {"num": evidence}, requested_level=OAKLevel.FORMALIZED)
    assert not decision.accepted
    assert decision.maximum_allowed_level <= OAKLevel.NUMERICALLY_TESTED
    assert any("formal proof" in blocker for blocker in decision.blockers)


def test_formal_and_independent_evidence_can_reach_oak7_without_declaring_truth_here():
    formal = Evidence("formal", EvidenceKind.FORMAL_PROOF, "checked term", digest="sha256:formal")
    review = Evidence("review", EvidenceKind.INDEPENDENT_REVIEW, "independent audit", source="review-id")
    claim = Claim(
        "restricted-result",
        ProblemId.POINCARE,
        ClaimKind.KNOWN_THEOREM,
        "restricted result",
        evidence_ids=("formal", "review"),
        oak_level=OAKLevel.INDEPENDENTLY_REVIEWED,
    )
    decision = evaluate_claim(claim, {"formal": formal, "review": review})
    assert decision.accepted
    assert decision.maximum_allowed_level == OAKLevel.INDEPENDENTLY_REVIEWED


def test_missing_evidence_fails_closed():
    claim = Claim("x", ProblemId.HODGE, ClaimKind.LEMMA, "x", evidence_ids=("missing",))
    decision = evaluate_claim(claim, {})
    assert not decision.accepted
    assert "missing evidence" in decision.blockers[0]


def test_dependency_level_limits_claim():
    manuscript = Evidence("m", EvidenceKind.MANUSCRIPT_PROOF, "proof manuscript")
    claim = Claim(
        "target", ProblemId.BSD, ClaimKind.LEMMA, "target", dependencies=("weak",),
        evidence_ids=("m",), oak_level=OAKLevel.GENERAL_MANUSCRIPT,
    )
    decision = evaluate_claim(claim, {"m": manuscript}, dependency_levels={"weak": OAKLevel.KNOWN_CASES})
    assert not decision.accepted
    assert decision.maximum_allowed_level == OAKLevel.KNOWN_CASES


def test_computation_is_capped_at_oak3():
    formal = Evidence("formal", EvidenceKind.FORMAL_PROOF, "formalized computation", digest="sha256:x")
    claim = Claim("calc", ProblemId.RIEMANN, ClaimKind.COMPUTATION, "finite computation", evidence_ids=("formal",), oak_level=OAKLevel.FORMALIZED)
    decision = evaluate_claim(claim, {"formal": formal})
    assert decision.maximum_allowed_level == OAKLevel.NUMERICALLY_TESTED


def _strategy(identifier: str, impact: float) -> StrategyScore:
    return StrategyScore(identifier, ProblemId.NAVIER_STOKES, .8, .8, .8, .7, impact, .4, .4, .4)


def test_strategy_ranking_is_deterministic():
    ranked = rank_strategies((_strategy("low", .3), _strategy("high", .9)))
    assert [item.strategy_id for item in ranked] == ["high", "low"]


def test_supportive_and_refuting_results_update_distinct_counts():
    strategy = _strategy("s", .8)
    updated = update_strategy(strategy, supportive_results=3, refuting_results=2)
    assert updated.evidence_for == 3
    assert updated.evidence_against == 2
    assert updated.posterior_weight != strategy.posterior_weight


def test_budget_allocation_is_exact_and_nonnegative():
    allocations = allocate_finite_budget((_strategy("a", .9), _strategy("b", .4), _strategy("c", .2)), total_budget_units=101)
    assert sum(item.finite_budget_units for item in allocations) == 101
    assert all(item.finite_budget_units >= 0 for item in allocations)
    assert sum(item.normalized_share for item in allocations) == pytest.approx(1.0)


def test_campaign_preserves_all_problem_keys_and_no_solution_claim():
    payload = compile_campaign(total_budget_units=127)
    assert payload["total_budget_units"] == 127
    assert set(payload["problem_budget_units"]) == {problem.value for problem in ProblemId}
    assert payload["solution_claimed"] is False
    assert payload["permanent_total_cap"] is None


def test_formal_export_contains_sorry_and_explicit_incompleteness():
    claim = Claim("a strange theorem", ProblemId.HODGE, ClaimKind.LEMMA, "A sample statement", assumptions=("A",))
    skeleton = export_lean_skeleton(claim)
    assert "sorry" in skeleton.text
    assert not skeleton.proof_complete
    assert skeleton.unresolved_obligations


def test_receipt_chain_round_trip():
    first = create_receipt(sequence=0, previous_digest=GENESIS, event_type="claim-created", payload={"id": "a"})
    second = create_receipt(sequence=1, previous_digest=first.receipt_digest, event_type="claim-tested", payload={"id": "a"})
    valid, errors = verify_chain((first, second))
    assert valid
    assert errors == ()


def test_receipt_tampering_detected():
    first = create_receipt(sequence=0, previous_digest=GENESIS, event_type="claim-created", payload={"id": "a"})
    tampered = replace(first, payload={"id": "b"})
    valid, errors = verify_chain((tampered,))
    assert not valid
    assert any("digest" in error for error in errors)


def test_benchmark_status_and_boundaries():
    report = run_benchmark()
    assert report["status"] == "CERTIFIED_SOFTWARE_FIXTURE_R0_1"
    assert report["registry_valid"] is True
    assert report["poincare_fixture_reaches_conclusion"] is True
    assert report["finite_test_is_not_proof"] is True
    assert report["solution_claimed"] is False


def test_campaign_digest_stable():
    assert compile_campaign(total_budget_units=100)["digest"] == compile_campaign(total_budget_units=100)["digest"]


def test_json_serializability_of_benchmark():
    json.dumps(run_benchmark(), default=str)
