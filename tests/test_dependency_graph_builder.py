from tools.dependency_graph_builder import DependencyEdge, build_dependency_graph


def test_dependency_graph_records_edges():
    edge = DependencyEdge("test_a", "tests", "tool_a")
    graph = build_dependency_graph((edge,), known_sources=("test_a",))
    assert graph.edges == (edge,)
    assert graph.orphan_sources == ()


def test_dependency_graph_detects_orphan_source():
    graph = build_dependency_graph((), known_sources=("tool_without_link",))
    assert graph.orphan_sources == ("tool_without_link",)
