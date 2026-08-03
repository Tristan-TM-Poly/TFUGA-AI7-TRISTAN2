import math,pytest
from omega_synergy_n_t.combinatorics import subsets,lattice_missing,mask_to_subset
from omega_synergy_n_t.fixtures import pure_triplet,reducible_triplet,anti_order4,synergy_os_order4
from omega_synergy_n_t.mobius import decompose_measurements,direct_interaction,mobius_decompose,zeta_reconstruct,validate_complete_lattice,interaction_standard_error


def values(records): return {r.key:r.value for r in records}

def find(estimates,components):
    target=tuple(sorted(components)); return next(x for x in estimates if x.components==target)

def test_subsets_boolean_count(): assert len(list(subsets(("A","B","C"))))==8
def test_mask_round_trip(): assert mask_to_subset(("A","B","C"),5)==("A","C")
def test_lattice_missing_empty_when_complete(): assert lattice_missing(("A","B"),{frozenset(),frozenset({"A"}),frozenset({"B"}),frozenset({"A","B"})})==[]
def test_validate_rejects_incomplete():
    with pytest.raises(ValueError): validate_complete_lattice({frozenset():0,frozenset({"A"}):1},("A","B"))
def test_pure_triplet_pairs_zero():
    out=decompose_measurements(pure_triplet())
    assert find(out,("A","B")).proper_interaction==pytest.approx(0)
    assert find(out,("A","B","C")).proper_interaction==pytest.approx(1)
def test_reducible_triplet_has_zero_triple(): assert find(decompose_measurements(reducible_triplet()),("A","B","C")).proper_interaction==pytest.approx(0)
def test_reducible_pair_exact(): assert find(decompose_measurements(reducible_triplet()),("A","B")).proper_interaction==pytest.approx(.5)
def test_anti_order4_detected(): assert find(decompose_measurements(anti_order4()),("A","B","C","D")).proper_interaction==pytest.approx(-2)
def test_synergy_os_order4_positive_net():
    x=find(decompose_measurements(synergy_os_order4()),("Foundry","Intent","Portfolio","Proof"))
    assert x.proper_interaction==pytest.approx(.7); assert x.net_synergy>0
def test_zeta_inverse_identity():
    interactions={frozenset():.2,frozenset({"A"}):1,frozenset({"B"}):2,frozenset({"A","B"}):.3}
    assert mobius_decompose(zeta_reconstruct(interactions))==pytest.approx(interactions)
def test_direct_equals_decomposition():
    v=values(reducible_triplet()); assert direct_interaction(v,("A","B","C"))==pytest.approx(mobius_decompose(v)[frozenset({"A","B","C"})])
def test_standard_error_rss():
    errors={frozenset(s):.1 for s in subsets(("A","B"))}
    assert interaction_standard_error(errors,("A","B"))==pytest.approx(.2)
def test_context_mix_rejected():
    records=pure_triplet(); records[0]=type(records[0])(records[0].components,records[0].value,context_id="other")
    with pytest.raises(ValueError): decompose_measurements(records)
def test_necessity_present():
    x=find(decompose_measurements(reducible_triplet()),("A","B","C")); assert set(x.necessity)=={"A","B","C"}
def test_purity_nonnegative(): assert all(x.purity>=0 for x in decompose_measurements(synergy_os_order4()))
