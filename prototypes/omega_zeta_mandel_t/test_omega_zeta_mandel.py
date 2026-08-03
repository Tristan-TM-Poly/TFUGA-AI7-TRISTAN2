"""OAK smoke tests for Omega Zeta-Mandel-Tristan."""

from omega_zeta_mandel import (
    basis_vector,
    cd_mul,
    cd_norm,
    mandelbrot_cvcd,
    riemann_zeta_eta,
    sedenion_mandelbrot_cvcd,
    zero_divisor_risk_probe,
)


def test_classic_mandelbrot_inside_and_outside():
    inside = mandelbrot_cvcd(0j, max_iter=32)
    outside = mandelbrot_cvcd(2 + 2j, max_iter=32)
    assert inside.escape_iter == 32
    assert outside.escape_iter < 4
    assert inside.oak.claim_status.startswith("numerical")


def test_eta_zeta_known_value_approx():
    value = riemann_zeta_eta(2 + 0j, terms=2000)
    assert abs(value.real - 1.644934) < 2e-3
    assert abs(value.imag) < 1e-9


def test_cayley_dickson_complex_unit_square():
    one_i = basis_vector(2, 1)
    product = cd_mul(one_i, one_i)
    assert abs(product[0] + 1.0) < 1e-12
    assert abs(product[1]) < 1e-12


def test_sedenion_kernel_has_oak_warning():
    c = tuple(-0.25 if i == 1 else 0.0 for i in range(16))
    signature = sedenion_mandelbrot_cvcd(c, max_iter=16)
    assert signature.oak.algebra.startswith("Sedenions")
    assert signature.uncertainty_u2 > 0.0


def test_zero_divisor_probe_range():
    x = basis_vector(16, 3)
    risk = zero_divisor_risk_probe(x)
    assert 0.0 <= risk <= 1.0 + 1e-12
    assert abs(cd_norm(x) - 1.0) < 1e-12
