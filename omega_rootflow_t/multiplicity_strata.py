"""Multiplicity-stratum geometry for Ω-ROOTFLOW-T∞ R0.7.

For a root ``c`` of exact multiplicity ``m>=2``:

    P^(q)(c)=0, q=0,...,m-1
    P^(m)(c)!=0.

With selected coefficient perturbations ``theta_j z^k_j``, differentiating the
vanishing derivative constraints gives a parameter tangent matrix

    A[q,j] = (k_j)_q c^(k_j-q), q=0,...,m-2,

where ``(k)_q`` is the falling factorial.  Parameter tangent directions lie in
``ker A``.  For each tangent direction ``v``, the final differentiated equation
gives the motion of the multiplicity-m root:

    dc = - sum_j (k_j)_(m-1) c^(k_j-m+1) v_j / P^(m)(c).

R0.7 computes this local complex tangent geometry and validates it by requiring
all derivative constraints through order ``m-1`` to have O(epsilon^2) residual
under the first-order predictor.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, polynomial_value
from .exact import ExactScalar, exact_coefficients, exact_polydivmod

ComplexArray = npt.NDArray[np.complex128]


def falling_factorial(value: int, order: int) -> int:
    if value < 0 or order < 0:
        raise ValueError("value and order must be non-negative")
    if order > value:
        return 0
    result = 1
    for offset in range(order):
        result *= value - offset
    return result


def _parameter_derivative(degree: int, order: int, root: complex) -> complex:
    factor = falling_factorial(degree, order)
    if factor == 0:
        return 0j
    return complex(factor) * root ** (degree - order)


def _degrees(values: npt.ArrayLike, polynomial_degree: int) -> tuple[int, ...]:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError("parameter_degrees must be a non-empty vector")
    result: list[int] = []
    for value in raw.tolist():
        integer = int(value)
        if integer != value:
            raise ValueError("parameter_degrees must contain integers")
        if not 0 <= integer <= polynomial_degree:
            raise ValueError("parameter degree outside polynomial coefficient range")
        if integer in result:
            raise ValueError("parameter_degrees must be unique")
        result.append(integer)
    return tuple(result)


def _rref_nullspace(matrix: ComplexArray, tolerance: float) -> tuple[ComplexArray, int]:
    """Deterministic RREF nullspace basis returned as row vectors."""
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    rows, columns = matrix.shape
    if rows == 0:
        return np.eye(columns, dtype=np.complex128), 0
    work = matrix.astype(np.complex128, copy=True)
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(columns):
        candidates = np.abs(work[pivot_row:, column]) if pivot_row < rows else np.asarray([])
        if candidates.size == 0:
            break
        local = int(np.argmax(candidates))
        if candidates[local] <= tolerance:
            continue
        selected = pivot_row + local
        if selected != pivot_row:
            work[[pivot_row, selected]] = work[[selected, pivot_row]]
        work[pivot_row] /= work[pivot_row, column]
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row, column]
            if abs(factor) > tolerance:
                work[row] -= factor * work[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break

    rank = len(pivot_columns)
    free_columns = [column for column in range(columns) if column not in pivot_columns]
    basis: list[ComplexArray] = []
    for free in free_columns:
        vector = np.zeros(columns, dtype=np.complex128)
        vector[free] = 1.0 + 0j
        for row, pivot in enumerate(pivot_columns):
            vector[pivot] = -work[row, free]
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        basis.append(vector)
    return (
        np.asarray(basis, dtype=np.complex128)
        if basis
        else np.empty((0, columns), dtype=np.complex128),
        rank,
    )


def _encode_vector(values: ComplexArray) -> list[list[float]]:
    return [[float(value.real), float(value.imag)] for value in values]


def _encode_matrix(values: ComplexArray) -> list[list[list[float]]]:
    return [_encode_vector(row) for row in values]


@dataclass(frozen=True)
class MultiplicityTangentSpace:
    critical_root: complex
    multiplicity: int
    parameter_degrees: tuple[int, ...]
    constraint_matrix: ComplexArray
    constraint_rank: int
    tangent_basis: ComplexArray
    root_velocities: ComplexArray
    derivative_residuals: tuple[float, ...]
    first_nonzero_derivative_magnitude: float
    tangent_constraint_residual: float
    tangent_dimension: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "critical_root": [float(self.critical_root.real), float(self.critical_root.imag)],
            "multiplicity": self.multiplicity,
            "parameter_degrees": list(self.parameter_degrees),
            "constraint_matrix": _encode_matrix(self.constraint_matrix),
            "constraint_rank": self.constraint_rank,
            "tangent_basis": _encode_matrix(self.tangent_basis),
            "root_velocities": _encode_vector(self.root_velocities),
            "derivative_residuals": list(self.derivative_residuals),
            "first_nonzero_derivative_magnitude": self.first_nonzero_derivative_magnitude,
            "tangent_constraint_residual": self.tangent_constraint_residual,
            "tangent_dimension": self.tangent_dimension,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def multiplicity_tangent_space(
    coefficients: npt.ArrayLike,
    critical_root: complex,
    multiplicity: int,
    parameter_degrees: npt.ArrayLike,
    *,
    vanishing_tolerance: float = 1e-9,
    nonzero_tolerance: float = 1e-10,
    rref_tolerance: float = 1e-11,
) -> MultiplicityTangentSpace:
    """Compute local complex tangent geometry for an exact multiplicity request."""
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    if not 2 <= multiplicity <= degree:
        raise ValueError("multiplicity must satisfy 2 <= m <= polynomial degree")
    if min(vanishing_tolerance, nonzero_tolerance, rref_tolerance) <= 0:
        raise ValueError("tolerances must be positive")
    degrees = _degrees(parameter_degrees, degree)
    c = complex(critical_root)

    residuals: list[float] = []
    for order in range(multiplicity):
        value = polynomial_value(coeffs, c) if order == 0 else derivative_value(coeffs, c, order=order)
        residuals.append(float(abs(value)))
    first_nonzero = derivative_value(coeffs, c, order=multiplicity)
    first_nonzero_magnitude = float(abs(first_nonzero))

    constraint = np.asarray(
        [
            [_parameter_derivative(k, order, c) for k in degrees]
            for order in range(multiplicity - 1)
        ],
        dtype=np.complex128,
    )

    if max(residuals) > vanishing_tolerance:
        return MultiplicityTangentSpace(
            critical_root=c,
            multiplicity=multiplicity,
            parameter_degrees=degrees,
            constraint_matrix=constraint,
            constraint_rank=0,
            tangent_basis=np.empty((0, len(degrees)), dtype=np.complex128),
            root_velocities=np.empty(0, dtype=np.complex128),
            derivative_residuals=tuple(residuals),
            first_nonzero_derivative_magnitude=first_nonzero_magnitude,
            tangent_constraint_residual=float("inf"),
            tangent_dimension=0,
            status="OAK_REFUSE_MULTIPLICITY_CONSTRAINTS_NOT_SATISFIED",
        )
    if first_nonzero_magnitude <= nonzero_tolerance:
        return MultiplicityTangentSpace(
            critical_root=c,
            multiplicity=multiplicity,
            parameter_degrees=degrees,
            constraint_matrix=constraint,
            constraint_rank=0,
            tangent_basis=np.empty((0, len(degrees)), dtype=np.complex128),
            root_velocities=np.empty(0, dtype=np.complex128),
            derivative_residuals=tuple(residuals),
            first_nonzero_derivative_magnitude=first_nonzero_magnitude,
            tangent_constraint_residual=float("inf"),
            tangent_dimension=0,
            status="OAK_REFUSE_MULTIPLICITY_HIGHER_THAN_REQUESTED",
        )

    tangent, rank = _rref_nullspace(constraint, rref_tolerance)
    final_parameter_row = np.asarray(
        [_parameter_derivative(k, multiplicity - 1, c) for k in degrees],
        dtype=np.complex128,
    )
    velocities = np.asarray(
        [-(final_parameter_row @ vector) / first_nonzero for vector in tangent],
        dtype=np.complex128,
    )
    constraint_error = (
        float(np.max(np.abs(constraint @ tangent.T))) if tangent.size else 0.0
    )
    status = (
        "OAK_PASS_MULTIPLICITY_TANGENT_SPACE"
        if constraint_error <= 1e-9
        else "OAK_WARN_MULTIPLICITY_TANGENT_RESIDUAL"
    )
    return MultiplicityTangentSpace(
        critical_root=c,
        multiplicity=multiplicity,
        parameter_degrees=degrees,
        constraint_matrix=constraint,
        constraint_rank=rank,
        tangent_basis=tangent,
        root_velocities=velocities,
        derivative_residuals=tuple(residuals),
        first_nonzero_derivative_magnitude=first_nonzero_magnitude,
        tangent_constraint_residual=constraint_error,
        tangent_dimension=int(tangent.shape[0]),
        status=status,
    )


@dataclass(frozen=True)
class MultiplicityPredictionAudit:
    multiplicity: int
    epsilon: float
    maximum_constraint_residual: float
    residuals_by_derivative_order: tuple[float, ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "multiplicity": self.multiplicity,
            "epsilon": self.epsilon,
            "maximum_constraint_residual": self.maximum_constraint_residual,
            "residuals_by_derivative_order": list(self.residuals_by_derivative_order),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_multiplicity_prediction(
    coefficients: npt.ArrayLike,
    tangent_space: MultiplicityTangentSpace,
    *,
    epsilon: float = 1e-4,
) -> MultiplicityPredictionAudit:
    coeffs = _coefficients(coefficients)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if tangent_space.status != "OAK_PASS_MULTIPLICITY_TANGENT_SPACE":
        raise ValueError("tangent_space must be a passing multiplicity tangent model")

    by_order = np.zeros(tangent_space.multiplicity, dtype=float)
    for vector, velocity in zip(tangent_space.tangent_basis, tangent_space.root_velocities, strict=True):
        perturbed = coeffs.copy()
        for local_index, coefficient_degree in enumerate(tangent_space.parameter_degrees):
            perturbed[coefficient_degree] += epsilon * vector[local_index]
        predicted_root = tangent_space.critical_root + epsilon * velocity
        for order in range(tangent_space.multiplicity):
            value = (
                polynomial_value(perturbed, predicted_root)
                if order == 0
                else derivative_value(perturbed, predicted_root, order=order)
            )
            by_order[order] = max(by_order[order], abs(value))

    maximum = float(np.max(by_order)) if by_order.size else 0.0
    status = (
        "OAK_PASS_MULTIPLICITY_TANGENT_PREDICTION"
        if maximum <= 1000.0 * epsilon**2
        else "OAK_WARN_MULTIPLICITY_TANGENT_PREDICTION"
    )
    return MultiplicityPredictionAudit(
        multiplicity=tangent_space.multiplicity,
        epsilon=float(epsilon),
        maximum_constraint_residual=maximum,
        residuals_by_derivative_order=tuple(float(value) for value in by_order),
        status=status,
    )


def _exact_scalar(value: ExactScalar) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        return Fraction(int(value), 1)
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value.strip())
    raise TypeError("exact root must be int, Fraction, or rational string")


def _exact_value(coefficients: tuple[Fraction, ...], root: Fraction) -> Fraction:
    value = Fraction(0)
    for coefficient in reversed(coefficients):
        value = value * root + coefficient
    return value


def exact_root_multiplicity(
    coefficients: Iterable[ExactScalar],
    root: ExactScalar,
) -> int:
    """Return exact multiplicity of a supplied rational root by repeated division."""
    polynomial = exact_coefficients(coefficients)
    c = _exact_scalar(root)
    factor = (-c, Fraction(1))
    multiplicity = 0
    current = polynomial
    while len(current) > 1 and _exact_value(tuple(current), c) == 0:
        quotient, remainder = exact_polydivmod(current, factor)
        if not (len(remainder) == 1 and remainder[0] == 0):
            break
        multiplicity += 1
        current = quotient
    return multiplicity
