"""Vieta/Newton/residue invariant calculus for Ω-ROOTFLOW-T∞ R0.5.

The module exposes exact algebraic identities and numerical cross-checks that
connect coefficient coordinates to root coordinates.  Coefficients are always
ascending ``[a0, ..., an]``.

For ``P(z)=a_n prod_j (z-r_j)``:

* elementary symmetric coordinates satisfy
  ``e_m(r)=(-1)^m a_{n-m}/a_n``;
* Newton sums ``p_m=sum_j r_j^m`` obey the standard coefficient recurrence;
* simple-root residue moments obey
  ``sum_j r_j^q/P'(r_j)=0`` for ``q<n-1`` and ``=1/a_n`` for ``q=n-1``;
* therefore, for non-leading coefficients,
  ``d p_m / d a_k = 0`` when ``m+k<n`` and ``=-m/a_n`` when ``m+k=n``.

The identities are classical algebra.  Ω-ROOTFLOW uses them as strong OAK
invariants for differential root calculations; no novelty/theorem claim is
attached to their mathematical truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, roots

ComplexArray = npt.NDArray[np.complex128]


def elementary_symmetric_from_coefficients(coefficients: npt.ArrayLike) -> ComplexArray:
    """Return ``[e0,...,en]`` with ``e0=1`` using Vieta coordinates."""
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    leading = coeffs[-1]
    result = np.empty(degree + 1, dtype=np.complex128)
    result[0] = 1.0 + 0j
    for order in range(1, degree + 1):
        result[order] = ((-1) ** order) * coeffs[degree - order] / leading
    return result


def elementary_symmetric_from_roots(root_values: npt.ArrayLike) -> ComplexArray:
    """Return elementary symmetric polynomials by direct root accumulation."""
    rr = np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")
    degree = rr.size
    result = np.zeros(degree + 1, dtype=np.complex128)
    result[0] = 1.0 + 0j
    for root in rr:
        for order in range(degree, 0, -1):
            result[order] += root * result[order - 1]
    return result


def vieta_jacobian(coefficients: npt.ArrayLike) -> ComplexArray:
    """Jacobian of ``(e1,...,en)`` with respect to ``(a0,...,an)``.

    The map is sparse.  Its radial/projective coefficient direction is null:
    ``J_vieta @ a = 0``.
    """
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    leading = coeffs[-1]
    elementary = elementary_symmetric_from_coefficients(coeffs)
    result = np.zeros((degree, degree + 1), dtype=np.complex128)
    for order in range(1, degree + 1):
        result[order - 1, degree - order] = ((-1) ** order) / leading
        result[order - 1, degree] = -elementary[order] / leading
    return result


def power_sums_from_roots(root_values: npt.ArrayLike, max_order: int) -> ComplexArray:
    """Return ``[p0,...,pM]`` where ``p0=n`` and ``p_m=sum r_j^m``."""
    rr = np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")
    if max_order < 0:
        raise ValueError("max_order must be non-negative")
    result = np.empty(max_order + 1, dtype=np.complex128)
    result[0] = complex(rr.size)
    for order in range(1, max_order + 1):
        result[order] = np.sum(rr**order)
    return result


def newton_power_sums(coefficients: npt.ArrayLike, max_order: int) -> ComplexArray:
    """Compute power sums from coefficients using Newton identities."""
    coeffs = _coefficients(coefficients)
    if max_order < 0:
        raise ValueError("max_order must be non-negative")
    degree = coeffs.size - 1
    # Descending normalized coefficients: [1,c1,...,cn].
    descending = (coeffs / coeffs[-1])[::-1]
    result = np.zeros(max_order + 1, dtype=np.complex128)
    result[0] = complex(degree)
    for order in range(1, max_order + 1):
        if order <= degree:
            total = sum(
                descending[index] * result[order - index]
                for index in range(1, order)
            )
            total += order * descending[order]
        else:
            total = sum(
                descending[index] * result[order - index]
                for index in range(1, degree + 1)
            )
        result[order] = -total
    return result


def residue_moments(
    coefficients: npt.ArrayLike,
    max_power: int,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return ``R_q=sum_j r_j^q/P'(r_j)`` for ``q=0..max_power``."""
    coeffs = _coefficients(coefficients)
    if max_power < 0:
        raise ValueError("max_power must be non-negative")
    if singularity_tolerance <= 0:
        raise ValueError("singularity_tolerance must be positive")
    rr = roots(coeffs)
    denominators = np.asarray([derivative_value(coeffs, complex(root)) for root in rr])
    if np.min(np.abs(denominators)) <= singularity_tolerance:
        raise np.linalg.LinAlgError("residue moments are ill-conditioned near a repeated root")
    result = np.empty(max_power + 1, dtype=np.complex128)
    for power in range(max_power + 1):
        result[power] = np.sum(rr**power / denominators)
    return result


def power_sum_jacobian(
    coefficients: npt.ArrayLike,
    max_order: int,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return ``d p_m / d a_k`` for ``m=1..max_order``.

    From implicit root differentiation,
    ``d p_m/d a_k = -m sum_j r_j^(m-1+k)/P'(r_j)``.
    """
    coeffs = _coefficients(coefficients)
    if max_order <= 0:
        raise ValueError("max_order must be positive")
    maximum_residue_power = max_order - 1 + (coeffs.size - 1)
    residues = residue_moments(
        coeffs,
        maximum_residue_power,
        singularity_tolerance=singularity_tolerance,
    )
    result = np.empty((max_order, coeffs.size), dtype=np.complex128)
    for order in range(1, max_order + 1):
        for coefficient_degree in range(coeffs.size):
            result[order - 1, coefficient_degree] = (
                -order * residues[order - 1 + coefficient_degree]
            )
    return result


def triangular_power_sum_sensitivity(coefficients: npt.ArrayLike) -> ComplexArray:
    """Expected exact triangular block for ``p_1..p_n`` vs ``a_0..a_{n-1}``.

    Entries beyond the first non-zero diagonal are left as NaN because they are
    polynomial-dependent rather than universal.
    """
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    leading = coeffs[-1]
    expected = np.full((degree, degree), np.nan + 0j, dtype=np.complex128)
    for order in range(1, degree + 1):
        for coefficient_degree in range(degree):
            total_degree = order + coefficient_degree
            if total_degree < degree:
                expected[order - 1, coefficient_degree] = 0j
            elif total_degree == degree:
                expected[order - 1, coefficient_degree] = -order / leading
    return expected


@dataclass(frozen=True)
class InvariantAudit:
    degree: int
    max_vieta_error: float
    max_newton_error: float
    max_residue_identity_error: float
    max_triangular_zero_error: float
    max_triangular_edge_error: float
    projective_vieta_null_error: float
    minimum_derivative: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.status == "OAK_PASS_VIETA_NEWTON_RESIDUE"

    def to_dict(self) -> dict[str, object]:
        return {
            "degree": self.degree,
            "max_vieta_error": self.max_vieta_error,
            "max_newton_error": self.max_newton_error,
            "max_residue_identity_error": self.max_residue_identity_error,
            "max_triangular_zero_error": self.max_triangular_zero_error,
            "max_triangular_edge_error": self.max_triangular_edge_error,
            "projective_vieta_null_error": self.projective_vieta_null_error,
            "minimum_derivative": self.minimum_derivative,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_invariants(
    coefficients: npt.ArrayLike,
    *,
    tolerance: float = 1e-8,
    singularity_tolerance: float = 1e-10,
) -> InvariantAudit:
    """Cross-check Vieta, Newton, residue and triangular sensitivity identities."""
    coeffs = _coefficients(coefficients)
    if tolerance <= 0 or singularity_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    degree = coeffs.size - 1
    rr = roots(coeffs)
    derivatives = np.asarray([abs(derivative_value(coeffs, complex(root))) for root in rr])
    minimum_derivative = float(np.min(derivatives))

    vieta_coeff = elementary_symmetric_from_coefficients(coeffs)
    vieta_roots = elementary_symmetric_from_roots(rr)
    max_vieta = float(np.max(np.abs(vieta_coeff - vieta_roots)))

    newton = newton_power_sums(coeffs, max(2 * degree, 1))
    direct = power_sums_from_roots(rr, max(2 * degree, 1))
    max_newton = float(np.max(np.abs(newton - direct)))

    if minimum_derivative <= singularity_tolerance:
        return InvariantAudit(
            degree=degree,
            max_vieta_error=max_vieta,
            max_newton_error=max_newton,
            max_residue_identity_error=float("inf"),
            max_triangular_zero_error=float("inf"),
            max_triangular_edge_error=float("inf"),
            projective_vieta_null_error=float(np.max(np.abs(vieta_jacobian(coeffs) @ coeffs))),
            minimum_derivative=minimum_derivative,
            status="OAK_WARN_NEAR_DISCRIMINANT",
        )

    residues = residue_moments(coeffs, degree - 1, singularity_tolerance=singularity_tolerance)
    expected_residues = np.zeros(degree, dtype=np.complex128)
    expected_residues[-1] = 1.0 / coeffs[-1]
    max_residue = float(np.max(np.abs(residues - expected_residues)))

    jacobian = power_sum_jacobian(
        coeffs,
        degree,
        singularity_tolerance=singularity_tolerance,
    )[:, :degree]
    triangular = triangular_power_sum_sensitivity(coeffs)
    finite_mask = np.isfinite(triangular.real)
    zero_mask = finite_mask & (np.abs(triangular) == 0)
    edge_mask = finite_mask & ~zero_mask
    max_zero = float(np.max(np.abs(jacobian[zero_mask]))) if np.any(zero_mask) else 0.0
    max_edge = (
        float(np.max(np.abs(jacobian[edge_mask] - triangular[edge_mask])))
        if np.any(edge_mask)
        else 0.0
    )
    projective_null = float(np.max(np.abs(vieta_jacobian(coeffs) @ coeffs)))

    worst = max(max_vieta, max_newton, max_residue, max_zero, max_edge, projective_null)
    status = (
        "OAK_PASS_VIETA_NEWTON_RESIDUE"
        if worst <= tolerance
        else "OAK_WARN_INVARIANT_RESIDUAL"
    )
    return InvariantAudit(
        degree=degree,
        max_vieta_error=max_vieta,
        max_newton_error=max_newton,
        max_residue_identity_error=max_residue,
        max_triangular_zero_error=max_zero,
        max_triangular_edge_error=max_edge,
        projective_vieta_null_error=projective_null,
        minimum_derivative=minimum_derivative,
        status=status,
    )
