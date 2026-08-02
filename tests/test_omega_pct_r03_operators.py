from fractions import Fraction

from omega_pct_t.r03max.model_generator import scalar_portal_candidate
from omega_pct_t.r03max.operators import OperatorGenerationBudget, generate_scalar_monomials, take


def test_operator_generation_is_lazy_and_dimension_bounded():
    theory = scalar_portal_candidate()
    generated = take(
        generate_scalar_monomials(
            theory,
            maximum_mass_dimension=Fraction(4),
            budget=OperatorGenerationBudget(max_bytes_estimate=100_000),
        ),
        20,
    )
    assert generated
    assert all(item.operator.declared_dimension is None for item in generated)
    assert all(item.score >= 0 for item in generated)


def test_quality_floor_can_prune_all_items():
    theory = scalar_portal_candidate()
    generated = tuple(
        generate_scalar_monomials(
            theory,
            maximum_mass_dimension=Fraction(4),
            budget=OperatorGenerationBudget(quality_floor=999),
        )
    )
    assert generated == ()
