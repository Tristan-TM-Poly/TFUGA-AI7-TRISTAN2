from sage_tristan.algebra_defect_lab import (
    aggregate_defects,
    complex_numbers_as_real_algebra,
    dual_numbers_as_real_algebra,
    l2_norm,
    vector_add,
    vector_sub,
)


def test_vector_helpers():
    assert vector_add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)
    assert vector_sub((1.0, 2.0), (3.0, 4.0)) == (-2.0, -2.0)
    assert l2_norm((3.0, 4.0)) == 5.0


def test_complex_algebra_multiplication():
    algebra = complex_numbers_as_real_algebra()
    one = algebra.basis_vector(0)
    i = algebra.basis_vector(1)
    assert algebra.multiply(one, i) == i
    assert algebra.multiply(i, i) == (-1.0, 0.0)


def test_complex_algebra_is_commutative_and_associative_on_basis():
    algebra = complex_numbers_as_real_algebra()
    assert algebra.is_commutative_on_basis()
    assert algebra.is_associative_on_basis()


def test_dual_numbers_have_nilpotent_generator():
    algebra = dual_numbers_as_real_algebra()
    eps = algebra.basis_vector(1)
    assert algebra.multiply(eps, eps) == (0.0, 0.0)


def test_defect_summary_contains_expected_keys():
    algebra = complex_numbers_as_real_algebra()
    summary = algebra.defect_summary((1.0, 2.0), (3.0, -1.0))
    assert set(summary) == {"commutator_norm", "associator_norm", "norm_defect"}
    assert summary["commutator_norm"] == 0.0
    assert summary["associator_norm"] == 0.0


def test_aggregate_defects():
    algebra = complex_numbers_as_real_algebra()
    sample = [algebra.basis_vector(0), algebra.basis_vector(1)]
    summary = aggregate_defects(algebra, sample)
    assert summary["mean_commutator_norm"] == 0.0
    assert summary["mean_associator_norm"] == 0.0
