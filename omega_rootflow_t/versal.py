"""Realified and local versal stratum calculus for Ω-ROOTFLOW-T∞ R0.8.

R0.7 describes the complex tangent space of a multiplicity-m stratum.  R0.8
adds two complementary views:

1. realification when selected coefficient parameters are constrained to be
   real;
2. a translation-normalized local unfolding jet for transverse directions.

At an exact multiplicity-m root c, R0.7 builds the complex constraint matrix

    A[q,j] = (k_j)_q c^(k_j-q), q=0,...,m-2.

For real parameter increments v, the actual linear constraints are

    Re(A) v = 0,  Im(A) v = 0.

Thus non-real collisions can have a larger real codimension than a naive
complex-rank count suggests.

For local splitting, write y=z-c and a_m=P^(m)(c)/m!.  After quotienting the
first-order translation direction (the y^(m-1) coefficient), the transverse
jet is

    y^m + sum_{q=0}^{m-2} u_q y^q,

with

    u_q = [sum_j binom(k_j,q)c^(k_j-q)dtheta_j] / a_m.

If the first non-zero jet term is q, the canonical balance predicts the local
Puiseux scale epsilon^(1/(m-q)).  This is a local truncated-model statement,
not a global theorem about an arbitrary parameter path.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, factorial

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value
from .multiplicity_strata import MultiplicityTangentSpace, multiplicity_tangent_space

ComplexArray = npt.NDArray[np.complex128]
FloatArray = npt.NDArray[np.float64]


def _real_rref_nullspace(matrix: FloatArray, tolerance: float) -> tuple[FloatArray, int]:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    rows, columns = matrix.shape
    if rows == 0:
        return np.eye(columns, dtype=float), 0
    work = matrix.astype(float, copy=True)
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
            factor_value = work[row, column]
            if abs(factor_value) > tolerance:
                work[row] -= factor_value * work[pivot_row]
        pivots.append(column)
        pivot_row += 1
    free = [column for column in range(columns) if column not in pivots]
    basis: list[FloatArray] = []
    for column in free:
        vector = np.zeros(columns, dtype=float)
        vector[column] = 1.0
        for row, pivot in enumerate(pivots):
            vector[pivot] = -work[row, column]
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        basis.append(vector)
    return (
        np.asarray(basis, dtype=float) if basis else np.empty((0, columns), dtype=float),
        len(pivots),
    )


def real_parameter_constraint_matrix(constraint_matrix: npt.ArrayLike) -> FloatArray:
    """Real matrix whose kernel is the real-parameter kernel of complex A."""
    matrix = np.asarray(constraint_matrix, dtype=np.complex128)
    if matrix.ndim != 2:
        raise ValueError("constraint_matrix must be two-dimensional")
    return np.vstack((matrix.real, matrix.imag)).astype(float, copy=False)


def complex_parameter_realification(constraint_matrix: npt.ArrayLike) -> FloatArray:
    """Realification of A acting on complex parameters x+iy."""
    matrix = np.asarray(constraint_matrix, dtype=np.complex128)
    if matrix.ndim != 2:
        raise ValueError("constraint_matrix must be two-dimensional")
    top = np.hstack((matrix.real, -matrix.imag))
    bottom = np.hstack((matrix.imag, matrix.real))
    return np.vstack((top, bottom)).astype(float, copy=False)


@dataclass(frozen=True)
class RealifiedTangentSpace:
    critical_root: complex
    multiplicity: int
    parameter_degrees: tuple[int, ...]
    complex_constraint_rank: int
    complex_tangent_dimension: int
    real_constraint_matrix: FloatArray
    real_constraint_rank: int
    real_tangent_basis: FloatArray
    real_tangent_dimension: int
    real_codimension: int
    tangent_constraint_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "critical_root": [float(self.critical_root.real), float(self.critical_root.imag)],
            "multiplicity": self.multiplicity,
            "parameter_degrees": list(self.parameter_degrees),
            "complex_constraint_rank": self.complex_constraint_rank,
            "complex_tangent_dimension": self.complex_tangent_dimension,
            "real_constraint_matrix": self.real_constraint_matrix.tolist(),
            "real_constraint_rank": self.real_constraint_rank,
            "real_tangent_basis": self.real_tangent_basis.tolist(),
            "real_tangent_dimension": self.real_tangent_dimension,
            "real_codimension": self.real_codimension,
            "tangent_constraint_residual": self.tangent_constraint_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def real_parameter_tangent_space(
    coefficients: npt.ArrayLike,
    critical_root: complex,
    multiplicity: int,
    parameter_degrees: npt.ArrayLike,
    *,
    tolerance: float = 1e-11,
) -> RealifiedTangentSpace:
    """Tangent geometry when selected coefficient increments must be real."""
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    complex_space = multiplicity_tangent_space(
        coefficients,
        critical_root,
        multiplicity,
        parameter_degrees,
        rref_tolerance=tolerance,
    )
    if complex_space.status != "OAK_PASS_MULTIPLICITY_TANGENT_SPACE":
        raise ValueError(f"multiplicity tangent model did not pass: {complex_space.status}")
    real_matrix = real_parameter_constraint_matrix(complex_space.constraint_matrix)
    basis, rank = _real_rref_nullspace(real_matrix, tolerance)
    residual = (
        float(np.max(np.abs(real_matrix @ basis.T))) if basis.size else 0.0
    )
    status = (
        "OAK_PASS_REAL_PARAMETER_TANGENT_SPACE"
        if residual <= 1e-9
        else "OAK_WARN_REAL_PARAMETER_TANGENT_RESIDUAL"
    )
    return RealifiedTangentSpace(
        critical_root=complex_space.critical_root,
        multiplicity=complex_space.multiplicity,
        parameter_degrees=complex_space.parameter_degrees,
        complex_constraint_rank=complex_space.constraint_rank,
        complex_tangent_dimension=complex_space.tangent_dimension,
        real_constraint_matrix=real_matrix,
        real_constraint_rank=rank,
        real_tangent_basis=basis,
        real_tangent_dimension=int(basis.shape[0]),
        real_codimension=rank,
        tangent_constraint_residual=residual,
        status=status,
    )


@dataclass(frozen=True)
class LocalUnfoldingMap:
    critical_root: complex
    multiplicity: int
    parameter_degrees: tuple[int, ...]
    leading_local_coefficient: complex
    jet_matrix: ComplexArray
    jet_rank: int
    unfolding_dimension: int
    complete_first_order_unfolding: bool
    tangent_dimension: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        def encode(value: complex) -> list[float]:
            return [float(value.real), float(value.imag)]
        return {
            "critical_root": encode(self.critical_root),
            "multiplicity": self.multiplicity,
            "parameter_degrees": list(self.parameter_degrees),
            "leading_local_coefficient": encode(self.leading_local_coefficient),
            "jet_matrix": [[encode(complex(value)) for value in row] for row in self.jet_matrix],
            "jet_rank": self.jet_rank,
            "unfolding_dimension": self.unfolding_dimension,
            "complete_first_order_unfolding": self.complete_first_order_unfolding,
            "tangent_dimension": self.tangent_dimension,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def local_unfolding_map(
    coefficients: npt.ArrayLike,
    critical_root: complex,
    multiplicity: int,
    parameter_degrees: npt.ArrayLike,
    *,
    rank_tolerance: float = 1e-10,
) -> LocalUnfoldingMap:
    """Compile coefficient directions to translation-normalized local split jets."""
    if rank_tolerance <= 0:
        raise ValueError("rank_tolerance must be positive")
    coeffs = _coefficients(coefficients)
    tangent = multiplicity_tangent_space(
        coeffs,
        critical_root,
        multiplicity,
        parameter_degrees,
    )
    if tangent.status != "OAK_PASS_MULTIPLICITY_TANGENT_SPACE":
        raise ValueError(f"multiplicity tangent model did not pass: {tangent.status}")
    c = tangent.critical_root
    leading = derivative_value(coeffs, c, order=multiplicity) / factorial(multiplicity)
    if abs(leading) <= rank_tolerance:
        raise ValueError("local leading coefficient is numerically zero")
    rows = []
    for order in range(multiplicity - 1):
        rows.append(
            [
                complex(comb(degree, order)) * c ** (degree - order) / leading
                if degree >= order
                else 0j
                for degree in tangent.parameter_degrees
            ]
        )
    jet = np.asarray(rows, dtype=np.complex128)
    rank = int(np.linalg.matrix_rank(jet, tol=rank_tolerance))
    target_dimension = multiplicity - 1
    complete = rank == target_dimension
    status = (
        "OAK_PASS_COMPLETE_LOCAL_UNFOLDING"
        if complete
        else "OAK_PASS_PARTIAL_LOCAL_UNFOLDING"
    )
    return LocalUnfoldingMap(
        critical_root=c,
        multiplicity=multiplicity,
        parameter_degrees=tangent.parameter_degrees,
        leading_local_coefficient=leading,
        jet_matrix=jet,
        jet_rank=rank,
        unfolding_dimension=target_dimension,
        complete_first_order_unfolding=complete,
        tangent_dimension=tangent.tangent_dimension,
        status=status,
    )


@dataclass(frozen=True)
class UnfoldingDirection:
    direction: ComplexArray
    local_jet: ComplexArray
    tangent_component: ComplexArray
    transverse_component: ComplexArray
    transverse_norm: float
    first_active_jet_order: int | None
    predicted_puiseux_exponent: float | None
    local_factor_order: int | None
    splitting_branch_count: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        def vector(values: ComplexArray) -> list[list[float]]:
            return [[float(value.real), float(value.imag)] for value in values]
        return {
            "direction": vector(self.direction),
            "local_jet": vector(self.local_jet),
            "tangent_component": vector(self.tangent_component),
            "transverse_component": vector(self.transverse_component),
            "transverse_norm": self.transverse_norm,
            "first_active_jet_order": self.first_active_jet_order,
            "predicted_puiseux_exponent": self.predicted_puiseux_exponent,
            "local_factor_order": self.local_factor_order,
            "splitting_branch_count": self.splitting_branch_count,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def analyze_unfolding_direction(
    unfolding: LocalUnfoldingMap,
    direction: npt.ArrayLike,
    *,
    activity_tolerance: float = 1e-10,
) -> UnfoldingDirection:
    """Decompose a coefficient direction into stratum-tangent/transverse parts."""
    if activity_tolerance <= 0:
        raise ValueError("activity_tolerance must be positive")
    vector = np.asarray(direction, dtype=np.complex128)
    if vector.ndim != 1 or vector.size != len(unfolding.parameter_degrees):
        raise ValueError("direction length must match parameter_degrees")
    jet = unfolding.jet_matrix @ vector
    transverse = np.linalg.pinv(unfolding.jet_matrix, rcond=activity_tolerance) @ jet
    tangent = vector - transverse
    transverse_norm = float(np.linalg.norm(transverse))
    active = [index for index, value in enumerate(jet) if abs(value) > activity_tolerance]
    if active:
        order = active[0]
        exponent = 1.0 / float(unfolding.multiplicity - order)
        branch_count = unfolding.multiplicity - order
        factor_order = order
        status = "OAK_PASS_TRANSVERSE_UNFOLDING_DIRECTION"
    else:
        order = None
        exponent = None
        branch_count = 0
        factor_order = None
        status = "OAK_PASS_FIRST_ORDER_STRATUM_TANGENT_DIRECTION"
    return UnfoldingDirection(
        direction=vector,
        local_jet=jet,
        tangent_component=tangent,
        transverse_component=transverse,
        transverse_norm=transverse_norm,
        first_active_jet_order=order,
        predicted_puiseux_exponent=exponent,
        local_factor_order=factor_order,
        splitting_branch_count=branch_count,
        status=status,
    )


def local_unfolding_roots(
    unfolding: LocalUnfoldingMap,
    direction: npt.ArrayLike,
    epsilon: float,
) -> ComplexArray:
    """Roots of the translation-normalized truncated local unfolding model."""
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    vector = np.asarray(direction, dtype=np.complex128)
    if vector.ndim != 1 or vector.size != len(unfolding.parameter_degrees):
        raise ValueError("direction length must match parameter_degrees")
    jet = unfolding.jet_matrix @ vector
    coefficients = np.zeros(unfolding.multiplicity + 1, dtype=np.complex128)
    coefficients[: unfolding.multiplicity - 1] = epsilon * jet
    coefficients[unfolding.multiplicity] = 1.0 + 0j
    offsets = np.polynomial.polynomial.polyroots(coefficients)
    return np.asarray(offsets + unfolding.critical_root, dtype=np.complex128)
