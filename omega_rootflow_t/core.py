"""Analytic differential mechanics of polynomial roots for Ω-ROOTFLOW-T∞.

Coefficient convention
----------------------
All coefficient arrays are in ascending order: ``[a0, a1, ..., an]`` for
``P(z) = a0 + a1*z + ... + an*z**n``.

For a simple root r of P, implicit differentiation gives

    dr = -dP(r) / P'(r)

and, in the monomial basis,

    ∂r/∂a_k = -r**k / P'(r).

The formulas are exact for simple roots. Near repeated roots P'(r) -> 0 and
first-order root coordinates become ill-conditioned; callers should treat the
reported singularity diagnostics as a hard OAK warning, not as a proof of a
stable continuation through the discriminant.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

ComplexArray = npt.NDArray[np.complex128]


def _coefficients(values: npt.ArrayLike) -> ComplexArray:
    coeffs = np.asarray(values, dtype=np.complex128)
    if coeffs.ndim != 1 or coeffs.size < 2:
        raise ValueError("coefficients must be a one-dimensional array of length >= 2")
    if not np.all(np.isfinite(coeffs.real)) or not np.all(np.isfinite(coeffs.imag)):
        raise ValueError("coefficients must be finite")
    if coeffs[-1] == 0:
        raise ValueError("leading coefficient must be non-zero")
    return coeffs


def polynomial_value(coefficients: npt.ArrayLike, z: complex | npt.ArrayLike) -> complex | ComplexArray:
    """Evaluate an ascending-order polynomial."""
    coeffs = _coefficients(coefficients)
    value = np.polynomial.polynomial.polyval(z, coeffs)
    if np.ndim(value) == 0:
        return complex(value)
    return np.asarray(value, dtype=np.complex128)


def derivative_coefficients(coefficients: npt.ArrayLike, order: int = 1) -> ComplexArray:
    """Return ascending coefficients of the requested derivative."""
    coeffs = _coefficients(coefficients)
    if order < 0:
        raise ValueError("order must be >= 0")
    result = coeffs.copy()
    for _ in range(order):
        if result.size <= 1:
            return np.zeros(1, dtype=np.complex128)
        result = np.arange(1, result.size, dtype=float) * result[1:]
    return np.asarray(result, dtype=np.complex128)


def derivative_value(coefficients: npt.ArrayLike, z: complex, order: int = 1) -> complex:
    """Evaluate P^(order)(z)."""
    coeffs = _coefficients(coefficients)
    if order < 0:
        raise ValueError("order must be >= 0")
    if order == 0:
        return complex(np.polynomial.polynomial.polyval(z, coeffs))
    d = coeffs.copy()
    for _ in range(order):
        if d.size <= 1:
            return 0j
        d = np.arange(1, d.size, dtype=float) * d[1:]
    return complex(np.polynomial.polynomial.polyval(z, d))


def roots(coefficients: npt.ArrayLike) -> ComplexArray:
    """Return all finite roots of a non-degenerate polynomial."""
    coeffs = _coefficients(coefficients)
    result = np.polynomial.polynomial.polyroots(coeffs)
    return np.asarray(result, dtype=np.complex128)


def monomial_basis(root: complex, count: int) -> ComplexArray:
    if count <= 0:
        raise ValueError("count must be positive")
    return np.asarray([root**k for k in range(count)], dtype=np.complex128)


def _safe_denominator(value: complex, tolerance: float, *, label: str = "P'(r)") -> complex:
    if tolerance <= 0:
        raise ValueError("singularity_tolerance must be positive")
    if abs(value) <= tolerance:
        raise np.linalg.LinAlgError(
            f"{label} is too small ({abs(value):.3e}); root-flow coordinates are singular or ill-conditioned"
        )
    return value


def root_differential(
    coefficients: npt.ArrayLike,
    root: complex,
    coefficient_differential: npt.ArrayLike,
    *,
    singularity_tolerance: float = 1e-12,
) -> complex:
    """Return dr for an arbitrary simultaneous differential da."""
    coeffs = _coefficients(coefficients)
    delta = np.asarray(coefficient_differential, dtype=np.complex128)
    if delta.shape != coeffs.shape:
        raise ValueError("coefficient_differential must match coefficients")
    denominator = _safe_denominator(derivative_value(coeffs, root), singularity_tolerance)
    delta_p = complex(np.polynomial.polynomial.polyval(root, delta))
    return -delta_p / denominator


def basis_root_differential(
    *,
    derivative_at_root: complex,
    basis_values_at_root: npt.ArrayLike,
    coefficient_differential: npt.ArrayLike,
    singularity_tolerance: float = 1e-12,
) -> complex:
    """Representation-invariant differential for P=sum a_k phi_k."""
    basis = np.asarray(basis_values_at_root, dtype=np.complex128)
    delta = np.asarray(coefficient_differential, dtype=np.complex128)
    if basis.ndim != 1 or delta.shape != basis.shape:
        raise ValueError("basis values and coefficient differential must be matching vectors")
    denominator = _safe_denominator(
        complex(derivative_at_root), singularity_tolerance, label="dP/dz"
    )
    return -complex(np.dot(basis, delta)) / denominator


def root_jacobian(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Jacobian J[j,k] = ∂r_j/∂a_k for all simple roots."""
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")
    result = np.empty((rr.size, coeffs.size), dtype=np.complex128)
    for j, root in enumerate(rr):
        denominator = _safe_denominator(
            derivative_value(coeffs, complex(root)), singularity_tolerance
        )
        result[j] = -monomial_basis(complex(root), coeffs.size) / denominator
    return result


def root_velocity(
    coefficients: npt.ArrayLike,
    coefficient_velocity: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return dr_j/dt for a coefficient path a(t)."""
    coeffs = _coefficients(coefficients)
    velocity = np.asarray(coefficient_velocity, dtype=np.complex128)
    if velocity.shape != coeffs.shape:
        raise ValueError("coefficient_velocity must match coefficients")
    jac = root_jacobian(coeffs, root_values, singularity_tolerance=singularity_tolerance)
    return jac @ velocity


def root_hessian(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return H[j,k,l] = ∂²r_j/(∂a_k ∂a_l) for simple roots."""
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    jac = root_jacobian(coeffs, rr, singularity_tolerance=singularity_tolerance)
    count = coeffs.size
    result = np.empty((rr.size, count, count), dtype=np.complex128)
    for j, root_value in enumerate(rr):
        root = complex(root_value)
        p1 = _safe_denominator(derivative_value(coeffs, root), singularity_tolerance)
        p2 = derivative_value(coeffs, root, order=2)
        for k in range(count):
            phi_k_prime = 0j if k == 0 else k * root ** (k - 1)
            for ell in range(count):
                phi_l_prime = 0j if ell == 0 else ell * root ** (ell - 1)
                result[j, k, ell] = -(
                    p2 * jac[j, k] * jac[j, ell]
                    + phi_k_prime * jac[j, ell]
                    + phi_l_prime * jac[j, k]
                ) / p1
    return result


def degree_perturbation_sensitivity(
    coefficients: npt.ArrayLike,
    root: complex,
    added_degree: int,
    *,
    singularity_tolerance: float = 1e-12,
) -> complex:
    """Sensitivity to adding epsilon*z**added_degree to P."""
    coeffs = _coefficients(coefficients)
    if added_degree < 0:
        raise ValueError("added_degree must be >= 0")
    p1 = _safe_denominator(derivative_value(coeffs, root), singularity_tolerance)
    return -(root**added_degree) / p1


def projective_scaling_residual(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return J*a; mathematically zero because P and λP have identical roots."""
    coeffs = _coefficients(coefficients)
    jac = root_jacobian(coeffs, root_values, singularity_tolerance=singularity_tolerance)
    return jac @ coeffs


@dataclass(frozen=True)
class RootCondition:
    root: complex
    derivative_magnitude: float
    reciprocal_derivative: float
    residual: float
    near_singular: bool


def root_conditions(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-10,
) -> tuple[RootCondition, ...]:
    """Diagnose residual and first-order sensitivity for each root."""
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    reports: list[RootCondition] = []
    for root_value in rr:
        root = complex(root_value)
        magnitude = abs(derivative_value(coeffs, root))
        reports.append(
            RootCondition(
                root=root,
                derivative_magnitude=float(magnitude),
                reciprocal_derivative=float(np.inf if magnitude == 0 else 1.0 / magnitude),
                residual=float(abs(polynomial_value(coeffs, root))),
                near_singular=bool(magnitude <= singularity_tolerance),
            )
        )
    return tuple(reports)
