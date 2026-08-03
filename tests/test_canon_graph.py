import pytest

from tools.canon_graph import CanonEdge, CanonGraph, CanonNode, CanonNodeType, CanonRelation


def test_add_node_and_edge_and_neighbors():
    graph = CanonGraph()
    graph.add_node(CanonNode("idea", "Idea", CanonNodeType.IDEA))
    graph.add_node(CanonNode("test", "Test", CanonNodeType.TEST))
    graph.add_edge(CanonEdge("e1", "test", "idea", CanonRelation.TESTS, confidence=0.8))
    assert graph.neighbors("test")[0].node_id == "idea"


def test_duplicate_node_rejected():
    graph = CanonGraph()
    node = CanonNode("idea", "Idea", CanonNodeType.IDEA)
    graph.add_node(node)
    with pytest.raises(ValueError):
        graph.add_node(node)


def test_orphan_nodes_and_contradictions():
    graph = CanonGraph()
    graph.add_node(CanonNode("a", "A", CanonNodeType.IDEA))
    graph.add_node(CanonNode("b", "B", CanonNodeType.IDEA))
    graph.add_node(CanonNode("c", "C", CanonNodeType.IDEA))
    graph.add_edge(CanonEdge("e1", "a", "b", CanonRelation.CONTRADICTS))
    assert len(graph.orphan_nodes()) == 1
    assert len(graph.contradiction_edges()) == 1
