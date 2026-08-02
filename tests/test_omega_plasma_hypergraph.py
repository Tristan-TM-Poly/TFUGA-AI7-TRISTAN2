from omega_plasma_t.hypergraph import *

def test_hypergraph_is_deterministic_and_auditable():
    h=PlasmaHypergraph(); h.add_node(Node("e","species","electron")); h.add_node(Node("field","field","electric field")); h.add_edge(Hyperedge("couple","lorentz",("field",),("e",)))
    assert len(h.fingerprint())==64
    assert h.audit()["status"]=="passed"

def test_missing_reference_is_blocked():
    h=PlasmaHypergraph(); h.add_node(Node("e","species","electron"))
    try: h.add_edge(Hyperedge("bad","x",("missing",),("e",)))
    except ValueError: pass
    else: raise AssertionError("missing node must be blocked")
