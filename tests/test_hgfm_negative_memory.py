from sage_tristan.hgfm_core import HGFMGraph, HGFMHyperEdge, HGFMNode, HGFMNodeState, build_claim_test_graph
from sage_tristan.negative_memory import NegativeMemoryBank, NegativeMemoryEntry, default_negative_memory_bank, filter_claims_by_negative_memory


def test_hgfm_add_nodes_edges_and_neighbors():
    graph = HGFMGraph()
    graph.add_node(HGFMNode(id="a", label="A", kind="claim"))
    graph.add_node(HGFMNode(id="b", label="B", kind="test"))
    graph.add_edge(HGFMHyperEdge(id="e", sources=("a",), targets=("b",), edge_type="tests"))
    assert graph.neighbors("a") == {"b"}
    assert graph.centrality_proxy()["a"] == 1
    assert graph.centrality_proxy()["b"] == 1


def test_hgfm_rejects_missing_nodes():
    graph = HGFMGraph()
    graph.add_node(HGFMNode(id="a", label="A", kind="claim"))
    try:
        graph.add_edge(HGFMHyperEdge(id="bad", sources=("a",), targets=("missing",), edge_type="tests"))
    except ValueError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("expected missing-node ValueError")


def test_hgfm_node_state_action_energy_bounds_values():
    state = HGFMNodeState(confidence=2.0, utility=1.0, fertility=1.0, testability=1.0, compressibility=1.0, risk=-1.0, oak_maturity=1.0)
    assert 0.0 <= state.action_energy() <= 1.0


def test_build_claim_test_graph():
    graph = build_claim_test_graph("claim", "test", "result", passed=True)
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.fertility_density() > 0


def test_negative_memory_bank_scans_and_scores():
    bank = NegativeMemoryBank()
    bank.add(
        NegativeMemoryEntry(
            id="n1",
            failure_type="missing_baseline",
            lesson="Need a baseline.",
            trigger_phrase="improves performance",
            replacement_rule="Add a baseline.",
        )
    )
    text = "This improves performance on my sample."
    assert bank.scan(text)
    assert bank.risk_score(text) == 1.0
    assert bank.replacement_rules_for(text) == ["Add a baseline."]


def test_default_negative_memory_bank_flags_overclaim_patterns():
    bank = default_negative_memory_bank()
    text = "The experiment proves the method improves performance."
    rules = bank.replacement_rules_for(text)
    assert len(rules) >= 2


def test_filter_claims_by_negative_memory():
    results = filter_claims_by_negative_memory(["This improves performance.", "Neutral formal definition."])
    assert results[0][1] > results[1][1]
