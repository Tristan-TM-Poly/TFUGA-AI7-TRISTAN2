"""Simultaneous multi-cluster root geometry for Ω-ROOTFLOW-T∞ R0.10.

R0.7 treats one multiplicity-m root. R0.10 stacks those local conditions for
several distinct root clusters and adds a fixed-location Hermite inverse-design
bridge.

For mobile clusters (c_alpha,m_alpha), preserving multiplicity to first order
requires, for q=0,...,m_alpha-2,

    sum_j (k_j)_q c_alpha^(k_j-q) dtheta_j = 0.

The stacked matrix is a confluent evaluation/Vandermonde-type matrix. Once a
parameter direction lies in its kernel, each cluster velocity follows from the
q=m_alpha-1 equation.

For fixed cluster locations, multiplicity m_alpha requires all Hermite
constraints q=0,...,m_alpha-1. These constraints are linear in polynomial
coefficients, so prescribed-location multiple-root design becomes a linear
least-squares / exact-residual problem once the root locations are fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, polynomial_value
from .multiplicity_strata import falling_factorial

ComplexArray = npt.NDArray[np.complex128]
FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class RootCluster:
    root: complex
    multiplicity: int

    def to_dict(self) -> dict[str, object]:
        return {
            "root": [float(self.root.real), float(self.root.imag)],
            "multiplicity": self.multiplicity,
        }


def _clusters(values: Iterable[RootCluster | tuple[complex, int]], degree: int) -> tuple[RootCluster, ...]:
    result: list[RootCluster] = []
    for value in values:
        cluster = value if isinstance(value, RootCluster) else RootCluster(complex(value[0]), int(value[1]))
        if cluster.multiplicity < 1:
            raise ValueError("cluster multiplicities must be positive")
        if cluster.multiplicity > degree:
            raise ValueError("cluster multiplicity exceeds polynomial degree")
        result.append(RootCluster(complex(cluster.root), int(cluster.multiplicity)))
    if not result:
        raise ValueError("at least one root cluster is required")
    for first in range(len(result)):
        for second in range(first + 1, len(result)):
            if abs(result[first].root - result[second].root) <= 1e-12:
                raise ValueError("cluster roots must be distinct")
    if sum(item.multiplicity for item in result) > degree:
        raise ValueError("total requested cluster multiplicity exceeds polynomial degree")
    return tuple(result)


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
            raise ValueError("parameter degree outside polynomial range")
        if integer in result:
            raise ValueError("parameter_degrees must be unique")
        result.append(integer)
    return tuple(result)


def confluent_evaluation(root: complex, derivative_order: int, degree: int) -> complex:
    factor = falling_factorial(degree, derivative_order)
    if factor == 0:
        return 0j
    return complex(factor) * complex(root) ** (degree - derivative_order)


def mobile_cluster_constraint_matrix(
    clusters: Sequence[RootCluster],
    parameter_degrees: Sequence[int],
) -> ComplexArray:
    rows: list[list[complex]] = []
    for cluster in clusters:
        for order in range(cluster.multiplicity - 1):
            rows.append([
                confluent_evaluation(cluster.root, order, degree)
                for degree in parameter_degrees
            ])
    return np.asarray(rows, dtype=np.complex128) if rows else np.empty((0, len(parameter_degrees)), dtype=np.complex128)


def fixed_cluster_hermite_matrix(
    clusters: Sequence[RootCluster],
    coefficient_degrees: Sequence[int],
) -> ComplexArray:
    rows: list[list[complex]] = []
    for cluster in clusters:
        for order in range(cluster.multiplicity):
            rows.append([
                confluent_evaluation(cluster.root, order, degree)
                for degree in coefficient_degrees
            ])
    return np.asarray(rows, dtype=np.complex128)


def _rref_nullspace(matrix: ComplexArray, tolerance: float) -> tuple[ComplexArray, int]:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    rows, columns = matrix.shape
    if rows == 0:
        return np.eye(columns, dtype=np.complex128), 0
    work = matrix.astype(np.complex128, copy=True)
    pivots: list[int] = []
    pivot_row = 0
    for column in range(columns):
        if pivot_row >= rows:
            break
        candidates = np.abs(work[pivot_row:, column])
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
        pivots.append(column)
        pivot_row += 1
    free = [column for column in range(columns) if column not in pivots]
    basis: list[ComplexArray] = []
    for free_column in free:
        vector = np.zeros(columns, dtype=np.complex128)
        vector[free_column] = 1.0
        for row, pivot in enumerate(pivots):
            vector[pivot] = -work[row, free_column]
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        basis.append(vector)
    return (
        np.asarray(basis, dtype=np.complex128) if basis else np.empty((0, columns), dtype=np.complex128),
        len(pivots),
    )


def _encode_vector(values: ComplexArray) -> list[list[float]]:
    return [[float(value.real), float(value.imag)] for value in values]


def _encode_matrix(values: ComplexArray) -> list[list[list[float]]]:
    return [_encode_vector(row) for row in values]


@dataclass(frozen=True)
class MultiClusterTangentSpace:
    clusters: tuple[RootCluster, ...]
    parameter_degrees: tuple[int, ...]
    constraint_matrix: ComplexArray
    constraint_rank: int
    expected_full_space_codimension: int
    tangent_basis: ComplexArray
    tangent_dimension: int
    cluster_velocities: ComplexArray
    maximum_cluster_constraint_residual: float
    tangent_constraint_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "clusters": [item.to_dict() for item in self.clusters],
            "parameter_degrees": list(self.parameter_degrees),
            "constraint_matrix": _encode_matrix(self.constraint_matrix),
            "constraint_rank": self.constraint_rank,
            "expected_full_space_codimension": self.expected_full_space_codimension,
            "tangent_basis": _encode_matrix(self.tangent_basis),
            "tangent_dimension": self.tangent_dimension,
            "cluster_velocities": _encode_matrix(self.cluster_velocities),
            "maximum_cluster_constraint_residual": self.maximum_cluster_constraint_residual,
            "tangent_constraint_residual": self.tangent_constraint_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def multi_cluster_tangent_space(
    coefficients: npt.ArrayLike,
    clusters: Iterable[RootCluster | tuple[complex, int]],
    parameter_degrees: npt.ArrayLike,
    *,
    vanishing_tolerance: float = 1e-9,
    nonzero_tolerance: float = 1e-10,
    rref_tolerance: float = 1e-11,
) -> MultiClusterTangentSpace:
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    specs = _clusters(clusters, degree)
    degrees = _degrees(parameter_degrees, degree)
    if min(vanishing_tolerance, nonzero_tolerance, rref_tolerance) <= 0:
        raise ValueError("tolerances must be positive")

    maximum_residual = 0.0
    denominators: list[complex] = []
    for cluster in specs:
        for order in range(cluster.multiplicity):
            value = polynomial_value(coeffs, cluster.root) if order == 0 else derivative_value(coeffs, cluster.root, order=order)
            maximum_residual = max(maximum_residual, float(abs(value)))
        denominator = derivative_value(coeffs, cluster.root, order=cluster.multiplicity)
        denominators.append(denominator)
        if abs(denominator) <= nonzero_tolerance:
            matrix = mobile_cluster_constraint_matrix(specs, degrees)
            return MultiClusterTangentSpace(specs, degrees, matrix, 0, sum(item.multiplicity - 1 for item in specs), np.empty((0, len(degrees)), dtype=np.complex128), 0, np.empty((0, len(specs)), dtype=np.complex128), maximum_residual, float("inf"), "OAK_REFUSE_CLUSTER_MULTIPLICITY_HIGHER_THAN_REQUESTED")
    matrix = mobile_cluster_constraint_matrix(specs, degrees)
    if maximum_residual > vanishing_tolerance:
        return MultiClusterTangentSpace(specs, degrees, matrix, 0, sum(item.multiplicity - 1 for item in specs), np.empty((0, len(degrees)), dtype=np.complex128), 0, np.empty((0, len(specs)), dtype=np.complex128), maximum_residual, float("inf"), "OAK_REFUSE_CLUSTER_CONSTRAINTS_NOT_SATISFIED")

    tangent, rank = _rref_nullspace(matrix, rref_tolerance)
    velocities = np.empty((tangent.shape[0], len(specs)), dtype=np.complex128)
    for tangent_index, vector in enumerate(tangent):
        for cluster_index, cluster in enumerate(specs):
            final_row = np.asarray([
                confluent_evaluation(cluster.root, cluster.multiplicity - 1, item)
                for item in degrees
            ], dtype=np.complex128)
            velocities[tangent_index, cluster_index] = -(final_row @ vector) / denominators[cluster_index]
    tangent_error = float(np.max(np.abs(matrix @ tangent.T))) if tangent.size and matrix.size else 0.0
    expected = sum(item.multiplicity - 1 for item in specs)
    full_degree_set = degrees == tuple(range(degree + 1))
    if full_degree_set and rank != expected:
        status = "OAK_WARN_MULTICLUSTER_UNEXPECTED_FULL_SPACE_RANK"
    elif tangent_error <= 1e-9:
        status = "OAK_PASS_MULTICLUSTER_TANGENT_SPACE"
    else:
        status = "OAK_WARN_MULTICLUSTER_TANGENT_RESIDUAL"
    return MultiClusterTangentSpace(
        clusters=specs,
        parameter_degrees=degrees,
        constraint_matrix=matrix,
        constraint_rank=rank,
        expected_full_space_codimension=expected,
        tangent_basis=tangent,
        tangent_dimension=int(tangent.shape[0]),
        cluster_velocities=velocities,
        maximum_cluster_constraint_residual=maximum_residual,
        tangent_constraint_residual=tangent_error,
        status=status,
    )


@dataclass(frozen=True)
class MultiClusterPredictionAudit:
    epsilon: float
    maximum_constraint_residual: float
    maximum_residual_by_cluster: tuple[float, ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "epsilon": self.epsilon,
            "maximum_constraint_residual": self.maximum_constraint_residual,
            "maximum_residual_by_cluster": list(self.maximum_residual_by_cluster),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_multi_cluster_prediction(
    coefficients: npt.ArrayLike,
    tangent_space: MultiClusterTangentSpace,
    *,
    epsilon: float = 1e-4,
) -> MultiClusterPredictionAudit:
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if tangent_space.status != "OAK_PASS_MULTICLUSTER_TANGENT_SPACE":
        raise ValueError("tangent_space must be a passing multicluster tangent model")
    coeffs = _coefficients(coefficients)
    by_cluster = np.zeros(len(tangent_space.clusters), dtype=float)
    for vector, velocities in zip(tangent_space.tangent_basis, tangent_space.cluster_velocities, strict=True):
        perturbed = coeffs.copy()
        for local_index, coefficient_degree in enumerate(tangent_space.parameter_degrees):
            perturbed[coefficient_degree] += epsilon * vector[local_index]
        for cluster_index, cluster in enumerate(tangent_space.clusters):
            predicted_root = cluster.root + epsilon * velocities[cluster_index]
            for order in range(cluster.multiplicity):
                value = polynomial_value(perturbed, predicted_root) if order == 0 else derivative_value(perturbed, predicted_root, order=order)
                by_cluster[cluster_index] = max(by_cluster[cluster_index], abs(value))
    maximum = float(np.max(by_cluster)) if by_cluster.size else 0.0
    status = "OAK_PASS_MULTICLUSTER_TANGENT_PREDICTION" if maximum <= 2000.0 * epsilon**2 else "OAK_WARN_MULTICLUSTER_TANGENT_PREDICTION"
    return MultiClusterPredictionAudit(float(epsilon), maximum, tuple(float(value) for value in by_cluster), status)


@dataclass(frozen=True)
class HermiteInverseDesign:
    clusters: tuple[RootCluster, ...]
    free_degrees: tuple[int, ...]
    real_coefficients: bool
    constraint_rank: int
    update_norm: float
    residual_before: float
    residual_after: float
    coefficient_update: ComplexArray
    coefficients: ComplexArray
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "clusters": [item.to_dict() for item in self.clusters],
            "free_degrees": list(self.free_degrees),
            "real_coefficients": self.real_coefficients,
            "constraint_rank": self.constraint_rank,
            "update_norm": self.update_norm,
            "residual_before": self.residual_before,
            "residual_after": self.residual_after,
            "coefficient_update": _encode_vector(self.coefficient_update),
            "coefficients": _encode_vector(self.coefficients),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def _hermite_residual(coefficients: ComplexArray, clusters: Sequence[RootCluster]) -> ComplexArray:
    values: list[complex] = []
    for cluster in clusters:
        for order in range(cluster.multiplicity):
            values.append(polynomial_value(coefficients, cluster.root) if order == 0 else derivative_value(coefficients, cluster.root, order=order))
    return np.asarray(values, dtype=np.complex128)


def hermite_inverse_design(
    coefficients: npt.ArrayLike,
    clusters: Iterable[RootCluster | tuple[complex, int]],
    *,
    free_degrees: npt.ArrayLike | None = None,
    real_coefficients: bool = False,
    tolerance: float = 1e-10,
) -> HermiteInverseDesign:
    """Minimum-norm coefficient update imposing fixed-location multiplicities."""
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    specs = _clusters(clusters, degree)
    degrees = tuple(range(degree)) if free_degrees is None else _degrees(free_degrees, degree)
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    full_degrees = tuple(range(degree + 1))
    hermite = fixed_cluster_hermite_matrix(specs, full_degrees)
    residual = _hermite_residual(coeffs, specs)
    matrix = hermite[:, degrees]
    if real_coefficients:
        if np.max(np.abs(coeffs.imag)) > tolerance:
            raise ValueError("real_coefficients=True requires real starting coefficients")
        real_matrix = np.vstack((matrix.real, matrix.imag))
        real_target = np.concatenate((-residual.real, -residual.imag))
        update_free, _, rank, _ = np.linalg.lstsq(real_matrix, real_target, rcond=tolerance)
        update_free = update_free.astype(np.complex128)
    else:
        update_free, _, rank, _ = np.linalg.lstsq(matrix, -residual, rcond=tolerance)
    update = np.zeros_like(coeffs)
    for local_index, coefficient_degree in enumerate(degrees):
        update[coefficient_degree] = update_free[local_index]
    designed = coeffs + update
    after = _hermite_residual(designed, specs)
    before_norm = float(np.max(np.abs(residual))) if residual.size else 0.0
    after_norm = float(np.max(np.abs(after))) if after.size else 0.0
    status = "OAK_PASS_HERMITE_INVERSE_DESIGN" if after_norm <= max(tolerance * 100.0, 1e-10) else "OAK_WARN_HERMITE_INVERSE_RESIDUAL"
    return HermiteInverseDesign(
        clusters=specs,
        free_degrees=degrees,
        real_coefficients=real_coefficients,
        constraint_rank=int(rank),
        update_norm=float(np.linalg.norm(update)),
        residual_before=before_norm,
        residual_after=after_norm,
        coefficient_update=update,
        coefficients=designed,
        status=status,
    )
