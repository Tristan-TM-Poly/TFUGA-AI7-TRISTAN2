from __future__ import annotations

from omega_invariant_operator_t import (
    BaselineOperator,
    SearchBiasLedger,
    apply_witness,
    check_invariants,
    complete_graph_edges,
    cycle_edges,
    evaluate_apoptosis,
    posthoc_exchange_name,
    synthesize_tsp_exchange,
    tsp_invariants,
)


def test_canonical_tsp_cycle_satisfies_declared_invariants() -> None:
    nodes = tuple(range(5))
    state = cycle_edges(nodes)
    report = check_invariants(state, tsp_invariants(nodes))
    assert report.ok
    assert set(report.passed) == {
        "edge_count_n",
        "endpoints_in_domain",
        "degree_two",
        "single_connected_component",
    }


def test_exact_synthesis_rediscovers_minimal_two_edge_exchange_structure() -> None:
    receipt = synthesize_tsp_exchange(tuple(range(5)))
    assert receipt.status == "PASS"
    assert receipt.finite_minimality_certified is True
    assert receipt.minimal_distance == 4
    assert receipt.witnesses
    assert {witness.exchange_signature for witness in receipt.witnesses} == {(2, 2)}


def test_posthoc_recognition_does_not_drive_search() -> None:
    receipt = synthesize_tsp_exchange(tuple(range(5)))
    assert receipt.bias.operator_library == ()
    assert receipt.bias.grammar_primitives == ("remove_element", "add_element")
    assert {posthoc_exchange_name(witness) for witness in receipt.witnesses} == {
        "2-edge-exchange (2-opt family)"
    }


def test_every_witness_is_nonidentity_and_preserves_all_invariants() -> None:
    nodes = tuple(range(6))
    receipt = synthesize_tsp_exchange(nodes, max_witnesses=32)
    assert receipt.status == "PASS"
    for witness in receipt.witnesses:
        assert witness.target != receipt.source
        assert apply_witness(receipt.source, witness) == witness.target
        assert check_invariants(witness.target, tsp_invariants(nodes)).ok


def test_search_biases_are_explicit() -> None:
    ledger = SearchBiasLedger()
    assert ledger.representation == "finite_set_state"
    assert ledger.objective == "minimum_nonidentity_symmetric_difference"
    assert ledger.backend == "exact_shell_enumeration"
    assert "not zero inductive bias" in ledger.caveat


def test_budget_exhaustion_fails_closed_without_minimality_claim() -> None:
    receipt = synthesize_tsp_exchange(tuple(range(5)), max_candidates=1)
    assert receipt.status == "HOLD"
    assert receipt.budget_exhausted is True
    assert receipt.finite_minimality_certified is False
    assert receipt.minimal_distance is None
    assert receipt.witnesses == ()


def test_deterministic_replay() -> None:
    first = synthesize_tsp_exchange(tuple(range(5)), max_witnesses=8)
    second = synthesize_tsp_exchange(tuple(range(5)), max_witnesses=8)
    assert first == second


def test_complete_graph_universe_is_only_representation_domain_not_operator_library() -> None:
    nodes = tuple(range(5))
    universe = complete_graph_edges(nodes)
    assert len(universe) == 10
    receipt = synthesize_tsp_exchange(nodes)
    assert receipt.universe_size == len(universe)
    assert receipt.theorem_claimed is False
    assert receipt.automatic_apoptosis is False


def test_apoptosis_holds_without_external_equivalence_and_benchmark_evidence() -> None:
    receipt = synthesize_tsp_exchange(tuple(range(5)))
    baselines = [BaselineOperator("human_two_edge_exchange", (2, 2))]
    decision = evaluate_apoptosis(receipt, baselines)
    assert decision.decision == "HOLD"
    assert "semantic_equivalence_evidence_required" in decision.reasons
    assert "benchmark_noninferiority_evidence_required" in decision.reasons
    assert decision.automatic_delete is False


def test_apoptosis_can_become_review_eligible_but_never_auto_delete() -> None:
    receipt = synthesize_tsp_exchange(tuple(range(5)))
    baselines = [BaselineOperator("human_two_edge_exchange", (2, 2))]
    decision = evaluate_apoptosis(
        receipt,
        baselines,
        semantic_equivalence_evidence=True,
        benchmark_noninferiority_evidence=True,
    )
    assert decision.decision == "ELIGIBLE_FOR_REVIEW"
    assert decision.automatic_delete is False
    assert decision.destructive_action_authorized is False
