from omega_pct_t.hypercomplex import associator, audit_basis, basis, cayley_dickson_multiply, norm


def test_real_unit_identity():
    one = basis(16, 0)
    vector = tuple(float(i) for i in range(16))
    assert cayley_dickson_multiply(one, vector) == vector
    assert cayley_dickson_multiply(vector, one) == vector


def test_sedenion_audit_detects_nonassociativity_and_zero_divisors():
    report = audit_basis(16, search_zero_divisors=True, max_candidates=2)
    assert report.max_associator_norm > 0
    assert report.zero_divisor_candidates


def test_complex_subalgebra_is_associative():
    e1 = basis(16, 1)
    value = associator(e1, e1, e1)
    assert norm(value) == 0
