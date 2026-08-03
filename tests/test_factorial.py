import pytest
from omega_synergy_n_t.factorial import full_factorial_design,fractional_half_design,mobius_contrast,orthogonal_effect,alias_groups
from omega_synergy_n_t.fixtures import pure_triplet


def values(records): return {r.key:r.value for r in records}
def test_full_factorial_run_count(): assert len(full_factorial_design(("A","B","C")).runs)==8
def test_full_factorial_replicates(): assert len(full_factorial_design(("A","B"),replicates=3).runs)==12
def test_full_factorial_identifies_all_nonempty_terms(): assert len(full_factorial_design(("A","B","C")).identifiable_terms)==7
def test_full_factorial_empty_rejected():
    with pytest.raises(ValueError): full_factorial_design(())
def test_full_factorial_cap():
    with pytest.raises(ValueError): full_factorial_design(tuple(map(str,range(17))))
def test_fractional_half_count(): assert len(fractional_half_design(("A","B","C","D")).runs)==8
def test_fractional_requires_three():
    with pytest.raises(ValueError): fractional_half_design(("A","B"))
def test_fractional_declares_aliases(): assert fractional_half_design(("A","B","C","D")).alias_groups
def test_mobius_contrast_pure_triple(): assert mobius_contrast(values(pure_triplet()),("A","B","C"))==pytest.approx(1)
def test_mobius_contrast_missing_rejected():
    with pytest.raises(ValueError): mobius_contrast({frozenset():0},("A",))
def test_orthogonal_effect_main():
    universe=("A","B"); outcomes={frozenset():0,frozenset({"A"}):2,frozenset({"B"}):0,frozenset({"A","B"}):2}
    assert orthogonal_effect(outcomes,universe,("A",))==pytest.approx(2)
def test_orthogonal_incomplete_rejected():
    with pytest.raises(ValueError): orthogonal_effect({frozenset():0},("A",),("A",))
def test_alias_groups_partition_terms():
    d=fractional_half_design(("A","B","C")); flat=[x for g in d.alias_groups for x in g]; assert flat
