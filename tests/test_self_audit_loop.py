from tools.canon_graph import CanonEdge, CanonGraph, CanonNode, CanonNodeType, CanonRelation
from tools.self_audit_loop import AuditSeverity, audit_canon_graph


def test_audit_finds_orphan_node():
    graph = CanonGraph()
    graph.add_node(CanonNode("orphan", "Orphan", CanonNodeType.IDEA))
    report = audit_canon_graph(graph)
    assert any(f.finding_type == "orphan_node" for f in report.findings)


def test_audit_finds_missing_tests_for_tools():
    graph = CanonGraph()
    graph.add_node(CanonNode("tool", "Tool", CanonNodeType.TOOL))
    graph.add_node(CanonNode("theory", "Theory", CanonNodeType.THEORY))
    graph.add_edge(CanonEdge("e1", "tool", "theory", CanonRelation.IMPLEMENTS))
    report = audit_canon_graph(graph)
    assert any(f.finding_type == "missing_tests" and f.severity == AuditSeverity.HIGH for f in report.findings)


def test_audit_finds_contradiction_edge():
    graph = CanonGraph()
    graph.add_node(CanonNode("a", "A", CanonNodeType.IDEA))
    graph.add_node(CanonNode("b", "B", CanonNodeType.IDEA))
    graph.add_edge(CanonEdge("e1", "a", "b", CanonRelation.CONTRADICTS))
    report = audit_canon_graph(graph)
    assert any(f.finding_type == "contradiction" for f in report.findings)
