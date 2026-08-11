"""Local multi-parameter discriminant geometry for Ω-ROOTFLOW-T∞ R0.6.

Let a polynomial ``P`` have a generic double root ``c``:

    P(c)=0,  P'(c)=0,  P''(c) != 0.

Perturb selected coefficients by complex parameters ``theta_j`` multiplying
``z**k_j``.  The first-order collision constraints are

    sum_j c**k_j dtheta_j = 0,
    P''(c) dc + sum_j k_j c**(k_j-1) dtheta_j = 0.

The first equation defines the parameter tangent space to the discriminant
stratum; the second gives the induced velocity of the colliding root along each
tangent direction.

This is local simple double-root geometry.  Higher multiplicities require more
vanishing derivative constraints and are intentionally not silently folded into
this model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, polynomial_value

ComplexArray = npt.NDArray[np.complex128]


def _degrees(values: npt.ArrayLike, degree: int) -> tuple[int, ...]:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError("parameter_degrees must be a non-empty vector")
    result: list[int] = []
    for value in raw.tolist():
        integer = int(value)
        if integer != value:
            raise ValueError("parameter_degrees must contain integers")
        if not 0 <= integer <= degree:
            raise ValueError("parameter degree is outside the polynomial coefficient range")
        if integer in result:
            raise ValueError("parameter_degrees must be unique")
        result.append(integer)
    return tuple(result)


def _complex_vector(values: ComplexArray) -> list[list[float]]:
    return [[float(value.real), float(value.imag)] for value in values]


def _complex_matrix(values: ComplexArray) -> list[list[list[float]]]:
    return [_complex_vector(row) for row in values]


@dataclass(frozen=True)
class CollisionTangentSpace:
    critical_root: complex
    parameter_degrees: tuple[int, ...]
    constraint_normal: ComplexArray
    tangent_basis: ComplexArray
    root_velocities: ComplexArray
    tangent_constraint_residuals: ComplexArray
    polynomial_residual: float
    derivative_residual: float
    second_derivative_magnitude: float
    tangent_dimension: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "critical_root": [float(self.critical_root.real), float(self.critical_root.imag)],
            "parameter_degrees": list(self.parameter_degrees),
            "constraint_normal": _complex_vector(self.constraint_normal),
            "tangent_basis": _complex_matrix(self.tangent_basis),
            "root_velocities": _complex_vector(self.root_velocities),
            "tangent_constraint_residuals": _complex_vector(self.tangent_constraint_residuals),
            "polynomial_residual": self.polynomial_residual,
            "derivative_residual": self.derivative_residual,
            "second_derivative_magnitude": self.second_derivative_magnitude,
            "tangent_dimension": self.tangent_dimension,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def collision_tangent_space(
    coefficients: npt.ArrayLike,
    critical_root: complex,
    parameter_degrees: npt.ArrayLike,
    *,
    collision_tolerance: float = 1e-9,
    second_derivative_tolerance: float = 1e-10,
) -> CollisionTangentSpace:
    """Return a deterministic complex tangent basis at a generic double root."""
    coeffs = _coefficients(coefficients)
    if collision_tolerance <= 0 or second_derivative_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    degree = coeffs.size - 1
    degrees = _degrees(parameter_degrees, degree)
    c = complex(critical_root)
    residual = float(abs(polynomial_value(coeffs, c)))
    derivative_residual = float(abs(derivative_value(coeffs, c)))
    second = derivative_value(coeffs, c, order=2)
    second_magnitude = float(abs(second))

    if residual > collision_tolerance or derivative_residual > collision_tolerance:
        return CollisionTangentSpace(
            critical_root=c,
            parameter_degrees=degrees,
            constraint_normal=np.asarray([c**k for k in degrees], dtype=np.complex128),
            tangent_basis=np.empty((0, len(degrees)), dtype=np.complex128),
            root_velocities=np.empty(0, dtype=np.complex128),
            tangent_constraint_residuals=np.empty(0, dtype=np.complex128),
            polynomial_residual=residual,
            derivative_residual=derivative_residual,
            second_derivative_magnitude=second_magnitude,
            tangent_dimension=0,
            status="OAK_REFUSE_NOT_ON_COLLISION",
        )
    if second_magnitude <= second_derivative_tolerance:
        return CollisionTangentSpace(
            critical_root=c,
            parameter_degrees=degrees,
            constraint_normal=np.asarray([c**k for k in degrees], dtype=np.complex128),
            tangent_basis=np.empty((0, len(degrees)), dtype=np.complex128),
            root_velocities=np.empty(0, dtype=np.complex128),
            tangent_constraint_residuals=np.empty(0, dtype=np.complex128),
            polynomial_residual=residual,
            derivative_residual=derivative_residual,
            second_derivative_magnitude=second_magnitude,
            tangent_dimension=0,
            status="OAK_REFUSE_HIGHER_MULTIPLICITY",
        )

    normal = np.asarray([c**k for k in degrees], dtype=np.complex128)
    parameter_count = len(degrees)
    normal_norm = float(np.linalg.norm(normal))

    if normal_norm == 0.0:
        # E.g. c=0 and all selected k>0.  The value constraint has no first-order
        # content in those directions, so the full selected parameter space is
        # tangent at first order.
        tangent = np.eye(parameter_count, dtype=np.complex128)
    else:
        pivot = int(np.argmax(np.abs(normal)))
        rows: list[ComplexArray] = []
        for column in range(parameter_count):
            if column == pivot:
                continue
            vector = np.zeros(parameter_count, dtype=np.complex128)
            vector[column] = 1.0 + 0j
            vector[pivot] = -normal[column] / normal[pivot]
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            rows.append(vector)
        tangent = (
            np.asarray(rows, dtype=np.complex128)
            if rows
            else np.empty((0, parameter_count), dtype=np.complex128)
        )

    derivative_parameter = np.asarray(
        [0j if k == 0 else k * c ** (k - 1) for k in degrees],
        dtype=np.complex128,
    )
    root_velocities = np.asarray(
        [-(derivative_parameter @ vector) / second for vector in tangent],
        dtype=np.complex128,
    )
    constraint_residuals = np.asarray(
        [normal @ vector for vector in tangent],
        dtype=np.complex128,
    )
    maximum_constraint = (
        float(np.max(np.abs(constraint_residuals))) if constraint_residuals.size else 0.0
    )
    status = (
        "OAK_PASS_COLLISION_TANGENT_SPACE"
        if maximum_constraint <= 1e-10
        else "OAK_WARN_COLLISION_TANGENT_RESIDUAL"
    )
    return CollisionTangentSpace(
        critical_root=c,
        parameter_degrees=degrees,
        constraint_normal=normal,
        tangent_basis=tangent,
        root_velocities=root_velocities,
        tangent_constraint_residuals=constraint_residuals,
        polynomial_residual=residual,
        derivative_residual=derivative_residual,
        second_derivative_magnitude=second_magnitude,
        tangent_dimension=int(tangent.shape[0]),
        status=status,
    )


@dataclass(frozen=True)
class TangentPredictionAudit:
    epsilon: float
    maximum_polynomial_residual: float
    maximum_derivative_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "epsilon": self.epsilon,
            "maximum_polynomial_residual": self.maximum_polynomial_residual,
            "maximum_derivative_residual": self.maximum_derivative_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_tangent_prediction(
    coefficients: npt.ArrayLike,
    tangent_space: CollisionTangentSpace,
    *,
    epsilon: float = 1e-4,
) -> TangentPredictionAudit:
    """Check first-order collision tangent predictions at a small finite epsilon."""
    coeffs = _coefficients(coefficients)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if not tangent_space.status.startswith("OAK_PASS"):
        raise ValueError("tangent_space must be a passing generic double-root tangent model")

    max_value = 0.0
    max_derivative = 0.0
    for vector, root_velocity in zip(
        tangent_space.tangent_basis,
        tangent_space.root_velocities,
        strict=True,
    ):
        perturbed = coeffs.copy()
        for local_index, coefficient_degree in enumerate(tangent_space.parameter_degrees):
            perturbed[coefficient_degree] += epsilon * vector[local_index]
        predicted_root = tangent_space.critical_root + epsilon * root_velocity
        value = abs(polynomial_value(perturbed, predicted_root))
        derivative = abs(derivative_value(perturbed, predicted_root))
        max_value = max(max_value, float(value))
        max_derivative = max(max_derivative, float(derivative))

    scale = epsilon**2
    status = (
        "OAK_PASS_COLLISION_TANGENT_PREDICTION"
        if max(max_value, max_derivative) <= 100.0 * scale
        else "OAK_WARN_COLLISION_TANGENT_PREDICTION"
    )
    return TangentPredictionAudit(
        epsilon=float(epsilon),
        maximum_polynomial_residual=max_value,
        maximum_derivative_residual=max_derivative,
        status=status,
    )
