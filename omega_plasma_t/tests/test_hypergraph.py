from omega_plasma_t.hypergraph import *
def test_hypergraph():
    h=PlasmaHypergraph(); h.add_node(Node("e","species","electron")); h.add_node(Node("field","field","electric field")); h.add_edge(Hyperedge("couple","lorentz",("field",),("e",)))
    assert len(h.fingerprint())==64 and h.audit()["status"]=="passed"
