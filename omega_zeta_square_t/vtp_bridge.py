"""Bridge R11 Hankel constraints to Tristan's existing omega_vtp_t TensorProdLift.

The exact sparse polynomial remains canonical. This adapter aligns its monomial
multi-indices with ``omega_vtp_t.tensor_prod_lift.multi_indices`` so the same
constraint can be evaluated as a linear functional of the existing lifted
feature vector.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from omega_vtp_t.tensor_prod_lift import multi_indices, tensor_prod_lift

from .symbolic_hankel import HankelPolynomialConstraint


@dataclass(frozen=True)
class VTPLinearForm:
    n_variables: int
    degree: int
    alphas: tuple[tuple[int, ...], ...]
    coefficients: tuple[Fraction, ...]
    basis: str = "monomial"
    source: str = "Omega-ZETA-SQUARE-R11"
    proves_rh: bool = False

    @property
    def nonzero_feature_count(self) -> int:
        return sum(coeff != 0 for coeff in self.coefficients)


def constraint_to_vtp_linear_form(
    constraint: HankelPolynomialConstraint,
) -> VTPLinearForm:
    """Align an exact R11 constraint with omega_vtp_t monomial feature order."""

    if not constraint.terms:
        raise ValueError("constraint contains no monomial terms")
    n_variables = len(constraint.terms[0].exponents)
    if any(len(term.exponents) != n_variables for term in constraint.terms):
        raise ValueError("constraint terms have inconsistent exponent dimensions")
    degree = constraint.max_total_degree
    alphas = multi_indices(n_variables, degree)
    sparse = {term.exponents: term.coefficient for term in constraint.terms}
    coefficients = tuple(sparse.get(alpha, Fraction(0)) for alpha in alphas)
    return VTPLinearForm(
        n_variables=n_variables,
        degree=degree,
        alphas=alphas,
        coefficients=coefficients,
    )


def evaluate_vtp_linear_form(
    values: Sequence[float],
    form: VTPLinearForm,
) -> float:
    """Numerically evaluate the aligned linear form using existing TensorProdLift.

    This floating evaluation is a cross-check of the exact sparse identity, not
    a replacement for exact arithmetic and not evidence of all-orders positivity.
    """

    if len(values) != form.n_variables:
        raise ValueError("input dimension does not match VTP linear form")
    lift = tensor_prod_lift(values, form.degree)
    if lift.alphas != form.alphas:
        raise RuntimeError("TensorProdLift alpha ordering changed unexpectedly")
    row = lift.features[0]
    return float(sum(float(coeff) * float(feature) for coeff, feature in zip(form.coefficients, row)))
