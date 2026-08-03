from omega_hqt_t.synthetic_quebec import build_synthetic_quebec

def test_synthetic_graph_is_valid_and_explicit():
    graph=build_synthetic_quebec(); assert graph.validate()==[]; assert len(graph.nodes)==38; assert len(graph.hyperedges)==37
    assert all(n.attributes.get("synthetic",False) or n.kind!="territory" for n in graph.nodes.values())

def test_projection_preserves_referential_integrity():
    graph=build_synthetic_quebec().projection(levels=("province","region")); assert graph.validate()==[]; assert len(graph.nodes)==18
