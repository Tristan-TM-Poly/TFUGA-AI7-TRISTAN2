"""Exact rational multi-cluster Hermite geometry for Ω-ROOTFLOW-T∞ R0.11.

This module is the exact-Q counterpart of the numerical R0.10 multicluster
layer.  It uses ``fractions.Fraction`` only and therefore has no numerical rank
threshold.

Supported exact operations:

* confluent mobile/fixed cluster matrices at rational cluster locations;
* exact RREF rank and nullspace;
* exact simultaneous mobile-cluster velocities;
* deterministic exact affine Hermite coefficient solve;
* exact post-design constraint audit.

The deterministic affine solver sets non-pivot free variables to zero. It is an
exact feasible solution, not an Euclidean minimum-norm claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence

from .exact import ExactPolynomial, ExactScalar, exact_coefficients, exact_determinant
from .multiplicity_strata import falling_factorial

ExactMatrix = tuple[tuple[Fraction, ...], ...]
ExactVector = tuple[Fraction, ...]


def _fraction(value: ExactScalar) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        return Fraction(int(value), 1)
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value.strip())
    raise TypeError("exact Hermite APIs accept int, Fraction, or rational string")


def _text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _vector_text(values: Sequence[Fraction]) -> list[str]:
    return [_text(value) for value in values]


def _matrix_text(matrix: ExactMatrix) -> list[list[str]]:
    return [_vector_text(row) for row in matrix]


@dataclass(frozen=True)
class ExactRootCluster:
    root: Fraction
    multiplicity: int

    def to_dict(self) -> dict[str, object]:
        return {"root": _text(self.root), "multiplicity": self.multiplicity}


def _clusters(
    values: Iterable[ExactRootCluster | tuple[ExactScalar, int]],
    degree: int,
) -> tuple[ExactRootCluster, ...]:
    result: list[ExactRootCluster] = []
    for value in values:
        if isinstance(value, ExactRootCluster):
            cluster = value
        else:
            cluster = ExactRootCluster(_fraction(value[0]), int(value[1]))
        if cluster.multiplicity < 1:
            raise ValueError("cluster multiplicities must be positive")
        if cluster.multiplicity > degree:
            raise ValueError("cluster multiplicity exceeds polynomial degree")
        normalized = ExactRootCluster(_fraction(cluster.root), int(cluster.multiplicity))
        if any(existing.root == normalized.root for existing in result):
            raise ValueError("cluster roots must be distinct")
        result.append(normalized)
    if not result:
        raise ValueError("at least one cluster is required")
    if sum(item.multiplicity for item in result) > degree:
        raise ValueError("total requested multiplicity exceeds polynomial degree")
    return tuple(result)


def _degrees(values: Iterable[int], degree: int) -> tuple[int, ...]:
    result: list[int] = []
    for raw in values:
        integer = int(raw)
        if integer != raw:
            raise ValueError("coefficient degrees must be integers")
        if not 0 <= integer <= degree:
            raise ValueError("coefficient degree outside polynomial range")
        if integer in result:
            raise ValueError("coefficient degrees must be unique")
        result.append(integer)
    if not result:
        raise ValueError("at least one coefficient degree is required")
    return tuple(result)


def exact_confluent_evaluation(root: ExactScalar, derivative_order: int, degree: int) -> Fraction:
    if derivative_order < 0:
        raise ValueError("derivative_order must be non-negative")
    if degree < 0:
        raise ValueError("degree must be non-negative")
    factor = falling_factorial(degree, derivative_order)
    if factor == 0:
        return Fraction(0)
    c = _fraction(root)
    return Fraction(factor) * c ** (degree - derivative_order)


def exact_mobile_cluster_matrix(
    clusters: Sequence[ExactRootCluster],
    parameter_degrees: Sequence[int],
) -> ExactMatrix:
    rows: list[ExactVector] = []
    for cluster in clusters:
        for order in range(cluster.multiplicity - 1):
            rows.append(tuple(
                exact_confluent_evaluation(cluster.root, order, degree)
                for degree in parameter_degrees
            ))
    return tuple(rows)


def exact_fixed_hermite_matrix(
    clusters: Sequence[ExactRootCluster],
    coefficient_degrees: Sequence[int],
) -> ExactMatrix:
    rows: list[ExactVector] = []
    for cluster in clusters:
        for order in range(cluster.multiplicity):
            rows.append(tuple(
                exact_confluent_evaluation(cluster.root, order, degree)
                for degree in coefficient_degrees
            ))
    return tuple(rows)


def exact_rref(
    matrix: Sequence[Sequence[Fraction]],
    augmented: Sequence[Fraction] | None = None,
) -> tuple[ExactMatrix, tuple[int, ...], ExactVector | None, bool]:
    rows = len(matrix)
    columns = len(matrix[0]) if rows else 0
    if any(len(row) != columns for row in matrix):
        raise ValueError("matrix rows must have equal length")
    if augmented is not None and len(augmented) != rows:
        raise ValueError("augmented vector length must equal row count")
    width = columns + (1 if augmented is not None else 0)
    work = [
        [Fraction(value) for value in row]
        + ([Fraction(augmented[index])] if augmented is not None else [])
        for index, row in enumerate(matrix)
    ]
    pivots: list[int] = []
    pivot_row = 0
    for column in range(columns):
        selected = next((row for row in range(pivot_row, rows) if work[row][column] != 0), None)
        if selected is None:
            continue
        if selected != pivot_row:
            work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot = work[pivot_row][column]
        work[pivot_row] = [value / pivot for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or work[row][column] == 0:
                continue
            factor = work[row][column]
            work[row] = [left - factor * right for left, right in zip(work[row], work[pivot_row], strict=True)]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    consistent = True
    if augmented is not None:
        for row in work:
            if all(row[column] == 0 for column in range(columns)) and row[-1] != 0:
                consistent = False
                break
    coefficient_part: ExactMatrix = tuple(tuple(row[:columns]) for row in work)
    rhs: ExactVector | None = tuple(row[-1] for row in work) if augmented is not None else None
    return coefficient_part, tuple(pivots), rhs, consistent


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    _, pivots, _, _ = exact_rref(matrix)
    return len(pivots)


def exact_nullspace(matrix: Sequence[Sequence[Fraction]]) -> tuple[ExactVector, ...]:
    reduced, pivots, _, _ = exact_rref(matrix)
    columns = len(reduced[0]) if reduced else (len(matrix[0]) if matrix else 0)
    free = [column for column in range(columns) if column not in pivots]
    basis: list[ExactVector] = []
    for free_column in free:
        vector = [Fraction(0)] * columns
        vector[free_column] = Fraction(1)
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free_column]
        basis.append(tuple(vector))
    return tuple(basis)


def exact_affine_solve(matrix: Sequence[Sequence[Fraction]], target: Sequence[Fraction]) -> ExactVector:
    reduced, pivots, rhs, consistent = exact_rref(matrix, target)
    if not consistent or rhs is None:
        raise ValueError("exact affine system is inconsistent")
    columns = len(reduced[0]) if reduced else (len(matrix[0]) if matrix else 0)
    solution = [Fraction(0)] * columns
    for row, pivot in enumerate(pivots):
        solution[pivot] = rhs[row]
    return tuple(solution)


def _derivative_value(polynomial: ExactPolynomial, root: Fraction, order: int) -> Fraction:
    total = Fraction(0)
    for degree, coefficient in enumerate(polynomial):
        if degree < order:
            continue
        total += coefficient * Fraction(falling_factorial(degree, order)) * root ** (degree - order)
    return total


def _dot(row: Sequence[Fraction], vector: Sequence[Fraction]) -> Fraction:
    return sum((left * right for left, right in zip(row, vector, strict=True)), Fraction(0))


@dataclass(frozen=True)
class ExactMultiClusterTangent:
    clusters: tuple[ExactRootCluster, ...]
    parameter_degrees: tuple[int, ...]
    constraint_matrix: ExactMatrix
    constraint_rank: int
    expected_full_space_codimension: int
    tangent_basis: tuple[ExactVector, ...]
    cluster_velocities: tuple[ExactVector, ...]
    exact_constraint_residual_zero: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "clusters": [item.to_dict() for item in self.clusters],
            "parameter_degrees": list(self.parameter_degrees),
            "constraint_matrix": _matrix_text(self.constraint_matrix),
            "constraint_rank": self.constraint_rank,
            "expected_full_space_codimension": self.expected_full_space_codimension,
            "tangent_basis": [_vector_text(vector) for vector in self.tangent_basis],
            "cluster_velocities": [_vector_text(vector) for vector in self.cluster_velocities],
            "exact_constraint_residual_zero": self.exact_constraint_residual_zero,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def exact_multi_cluster_tangent(
    coefficients: Iterable[ExactScalar],
    clusters: Iterable[ExactRootCluster | tuple[ExactScalar, int]],
    parameter_degrees: Iterable[int],
) -> ExactMultiClusterTangent:
    polynomial = exact_coefficients(coefficients)
    degree = len(polynomial) - 1
    specs = _clusters(clusters, degree)
    degrees = _degrees(parameter_degrees, degree)
    for cluster in specs:
        for order in range(cluster.multiplicity):
            if _derivative_value(polynomial, cluster.root, order) != 0:
                raise ValueError("requested exact cluster constraints are not satisfied")
        if _derivative_value(polynomial, cluster.root, cluster.multiplicity) == 0:
            raise ValueError("true cluster multiplicity is higher than requested")
    matrix = exact_mobile_cluster_matrix(specs, degrees)
    rank = exact_rank(matrix)
    basis = exact_nullspace(matrix)
    velocities: list[ExactVector] = []
    for vector in basis:
        one_vector: list[Fraction] = []
        for cluster in specs:
            final_row = tuple(
                exact_confluent_evaluation(cluster.root, cluster.multiplicity - 1, coefficient_degree)
                for coefficient_degree in degrees
            )
            denominator = _derivative_value(polynomial, cluster.root, cluster.multiplicity)
            one_vector.append(-_dot(final_row, vector) / denominator)
        velocities.append(tuple(one_vector))
    residual_zero = all(_dot(row, vector) == 0 for row in matrix for vector in basis)
    expected = sum(item.multiplicity - 1 for item in specs)
    full = degrees == tuple(range(degree + 1))
    status = (
        "OAK_PASS_EXACT_MULTICLUSTER_TANGENT"
        if residual_zero and (not full or rank == expected)
        else "OAK_FAIL_EXACT_MULTICLUSTER_TANGENT"
    )
    return ExactMultiClusterTangent(
        specs,
        degrees,
        matrix,
        rank,
        expected,
        basis,
        tuple(velocities),
        residual_zero,
        status,
    )


@dataclass(frozen=True)
class ExactHermiteDesign:
    clusters: tuple[ExactRootCluster, ...]
    free_degrees: tuple[int, ...]
    constraint_matrix: ExactMatrix
    constraint_rank: int
    square_constraint_determinant: Fraction | None
    coefficient_update: ExactVector
    coefficients: ExactPolynomial
    exact_residual_zero: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "clusters": [item.to_dict() for item in self.clusters],
            "free_degrees": list(self.free_degrees),
            "constraint_matrix": _matrix_text(self.constraint_matrix),
            "constraint_rank": self.constraint_rank,
            "square_constraint_determinant": None if self.square_constraint_determinant is None else _text(self.square_constraint_determinant),
            "coefficient_update": _vector_text(self.coefficient_update),
            "coefficients": _vector_text(self.coefficients),
            "exact_residual_zero": self.exact_residual_zero,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def exact_hermite_design(
    coefficients: Iterable[ExactScalar],
    clusters: Iterable[ExactRootCluster | tuple[ExactScalar, int]],
    *,
    free_degrees: Iterable[int] | None = None,
) -> ExactHermiteDesign:
    polynomial = exact_coefficients(coefficients)
    degree = len(polynomial) - 1
    specs = _clusters(clusters, degree)
    degrees = tuple(range(degree)) if free_degrees is None else _degrees(free_degrees, degree)
    all_degrees = tuple(range(degree + 1))
    full_matrix = exact_fixed_hermite_matrix(specs, all_degrees)
    matrix = tuple(tuple(row[degree_index] for degree_index in degrees) for row in full_matrix)
    residual = tuple(_dot(row, polynomial) for row in full_matrix)
    update_free = exact_affine_solve(matrix, tuple(-value for value in residual))
    update = [Fraction(0)] * (degree + 1)
    for local_index, degree_index in enumerate(degrees):
        update[degree_index] = update_free[local_index]
    designed = tuple(polynomial[index] + update[index] for index in range(degree + 1))
    after = tuple(_dot(row, designed) for row in full_matrix)
    rank = exact_rank(matrix)
    determinant = exact_determinant(matrix) if len(matrix) == len(degrees) and len(matrix) > 0 else None
    passed = all(value == 0 for value in after)
    status = "OAK_PASS_EXACT_HERMITE_DESIGN" if passed else "OAK_FAIL_EXACT_HERMITE_DESIGN"
    return ExactHermiteDesign(
        clusters=specs,
        free_degrees=degrees,
        constraint_matrix=matrix,
        constraint_rank=rank,
        square_constraint_determinant=determinant,
        coefficient_update=tuple(update),
        coefficients=designed,
        exact_residual_zero=passed,
        status=status,
    )
