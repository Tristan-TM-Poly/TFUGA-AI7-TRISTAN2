from fractions import Fraction

from omega_pct_t.r03max.lagrangian_ir import LagrangianCompiler, operator_mass_dimension
from omega_pct_t.r03max.model_generator import dark_vector_candidate, scalar_portal_candidate


def test_scalar_portal_dimension_four():
    theory = scalar_portal_candidate()
    operator = theory.operators[0]
    assert operator_mass_dimension(operator, theory) == Fraction(4)
    result = LagrangianCompiler().compile(theory)
    assert result.passed_structural_compilation
    assert result.operators[0].gauge_invariant_u1


def test_dark_vector_kinetic_mixing_dimension_four():
    theory = dark_vector_candidate()
    result = LagrangianCompiler().compile(theory)
    assert result.operators[0].mass_dimension == 4
    assert result.operators[0].coupling_mass_dimension == 0


def test_compilation_fingerprint_is_deterministic():
    compiler = LagrangianCompiler()
    assert compiler.compile(scalar_portal_candidate()).fingerprint == compiler.compile(
        scalar_portal_candidate()
    ).fingerprint
