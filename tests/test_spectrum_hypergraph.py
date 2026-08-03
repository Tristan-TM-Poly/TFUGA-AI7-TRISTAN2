import pytest
from omega_synergy_n_t.fixtures import pure_triplet,synergy_os_order4
from omega_synergy_n_t.mobius import decompose_measurements
from omega_synergy_n_t.spectrum import order_spectrum,genuine_interaction_rate,n_order_yield,higher_order_debt_ratio
from omega_synergy_n_t.hypergraph import SynergyComplex
from omega_synergy_n_t.minimality import necessity,minimal_cores,redundant_components,harmful_components


def test_spectrum_dominant_order_pure_triplet(): assert order_spectrum(decompose_measurements(pure_triplet())).dominant_order==3
def test_spectrum_entropy_nonnegative(): assert order_spectrum(decompose_measurements(synergy_os_order4())).order_entropy>=0
def test_spectrum_bands_sorted():
    s=order_spectrum(decompose_measurements(synergy_os_order4())); assert [b.order for b in s.bands]==sorted(b.order for b in s.bands)
def test_gir(): assert genuine_interaction_rate(decompose_measurements(pure_triplet()),3)==1
def test_yield_positive(): assert n_order_yield(decompose_measurements(synergy_os_order4()),4,2)>0
def test_yield_cost_validation():
    with pytest.raises(ValueError): n_order_yield([],2,0)
def test_debt_ratio_nonnegative(): assert higher_order_debt_ratio(decompose_measurements(synergy_os_order4()),4)>=0
def test_hypergraph_closure_missing():
    h=SynergyComplex(); h.add_edge(("A","B")); assert ("A",) in h.missing_faces(("A","B","C"))
def test_hypergraph_closure_observed():
    h=SynergyComplex(); h.add_edge(("A",)); h.add_edge(("B",)); h.add_edge(("A","B")); assert not h.missing_faces(("A","B"))
def test_hypergraph_components():
    h=SynergyComplex(); h.add_edge(("A","B")); h.add_edge(("C",)); assert h.connected_components()==[("A","B"),("C",)]
def test_hypergraph_incidence():
    h=SynergyComplex(); e=h.add_edge(("A","B")); assert e.id in h.incidence()["A"]
def test_minimal_core():
    v={frozenset():0,frozenset({"A"}):1,frozenset({"B"}):0,frozenset({"A","B"}):1}; assert minimal_cores(v,("A","B"),1)==[("A",)]
def test_redundant_component():
    v={frozenset({"A","B"}):1,frozenset({"A"}):1,frozenset({"B"}):0}; assert redundant_components(v,("A","B"))==["B"]
def test_harmful_component():
    v={frozenset({"A","B"}):.5,frozenset({"A"}):1,frozenset({"B"}):0}; assert harmful_components(v,("A","B"))==["B"]
def test_necessity_values():
    v={frozenset({"A","B"}):3,frozenset({"A"}):1,frozenset({"B"}):2}; assert necessity(v,("A","B"))=={"A":1,"B":2}
