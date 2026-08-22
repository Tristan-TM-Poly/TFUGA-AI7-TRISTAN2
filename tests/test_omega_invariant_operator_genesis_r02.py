from __future__ import annotations

import pytest

from omega_invariant_operator_t import (
    GraphInvariantGrammarLedger,
    cycle_edges,
    mine_graph_problem,
    synthesize_from_problem,
)


def fixture_traces():
    nodes = (0, 1, 2, 3, 4)
    training = (
        cycle_edges((0, 1, 2, 3, 4)),
        cycle_edges((0, 1, 3, 4, 2)),
    )
    holdout = (
        cycle_edges((0, 2, 1, 4, 3)),
        cycle_edges((0, 3, 1, 2, 4)),
    )
    return nodes, training, holdout


def test_trace_miner_recovers_structural_cycle_hypotheses_without_tsp_invariant_input() -> None:
    nodes, training, holdout = fixture_traces()
    problem = mine_graph_problem(nodes, training, holdout)
    accepted = {(item.kind, item.parameter) for item in problem.accepted_hypotheses}
    assert ("edge_count_eq", 5) in accepted
    assert ("endpoints_in_domain", None) in accepted
    assert ("uniform_degree_eq", 2) in accepted
    assert ("component_count_eq", 1) in accepted
    assert problem.status == "TRACE_SUPPORTED"


def test_holdout_kills_training_specific_persistent_edges() -> None:
    nodes, training, holdout = fixture_traces()
    problem = mine_graph_problem(nodes, training, holdout)
    rejected = [item for item in problem.rejected_hypotheses if item.kind == "contains_edge"]
    assert rejected
    assert all(item.training_support == 1.0 for item in rejected)
    assert all(item.holdout_support is not None and item.holdout_support < 1.0 for item in rejected)


def test_no_holdout_fails_closed_before_operator_synthesis() -> None:
    nodes, training, _ = fixture_traces()
    problem = mine_graph_problem(nodes, training)
    assert problem.status == "HOLD"
    assert all(item.status == "TRAIN_SUPPORTED" for item in problem.hypotheses)
    with pytest.raises(ValueError, match="held-out trace"):
        synthesize_from_problem(problem)


def test_problem_genesis_never_authorizes_objectives_or_interventions() -> None:
    nodes, training, holdout = fixture_traces()
    problem = mine_graph_problem(nodes, training, holdout)
    assert problem.objective is None
    assert problem.objective_authorized is False
    assert problem.intervention_authorized is False
    assert problem.theorem_claimed is False


def test_mined_problem_feeds_exact_oracle_and_rediscovers_two_remove_two_add_shell() -> None:
    nodes, training, holdout = fixture_traces()
    problem = mine_graph_problem(nodes, training, holdout)
    receipt = synthesize_from_problem(problem, max_witnesses=16)
    assert receipt.status == "PASS"
    assert receipt.finite_minimality_certified is True
    assert receipt.minimal_distance == 4
    assert {witness.exchange_signature for witness in receipt.witnesses} == {(2, 2)}


def test_grammar_ablation_changes_the_discovered_minimal_operator() -> None:
    nodes, training, holdout = fixture_traces()
    full_problem = mine_graph_problem(nodes, training, holdout)
    weak_grammar = GraphInvariantGrammarLedger(
        feature_templates=("constant_edge_count", "endpoint_domain")
    )
    weak_problem = mine_graph_problem(nodes, training, holdout, grammar=weak_grammar)

    full = synthesize_from_problem(full_problem, max_witnesses=8)
    weak = synthesize_from_problem(weak_problem, max_witnesses=8)

    assert full.minimal_distance == 4
    assert weak.minimal_distance == 2
    assert full.bias.operator_library == ()
    assert weak.bias.operator_library == ()


def test_grammar_ledger_makes_problem_genesis_bias_explicit() -> None:
    nodes, training, holdout = fixture_traces()
    problem = mine_graph_problem(nodes, training, holdout)
    assert problem.grammar.representation == "undirected_simple_edge_set"
    assert problem.grammar.validation == "held_out_positive_trace"
    assert "human-declared" in problem.grammar.caveat
    assert "feature grammar != discovered mathematics" in problem.oak_boundaries
