"""R0.3 active-factorization, polar-log, and morphism-codex layer.

The routines remain deliberately finite-dimensional and real. They add
structure without pretending that every map has one intrinsic real logarithm.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan2, log, sqrt
from typing import Mapping, Sequence

from .core import (
    BranchLedger,
    Matrix,
    add,
    commutator,
    determinant,
    frobenius_norm,
    identity,
    matrix,
    matrix_exponential,
    multiply,
    rank,
    relative_reconstruction_error,
    scale,
    shape,
    transpose,
    zeros,
)

_EPS = 1.0e-12


def matrix_inverse(value: Matrix, *, tolerance: float = 1.0e-12) -> Matrix:
    rows, columns = shape(value)
    if rows != columns:
        raise ValueError("Matrix inverse requires a square matrix")
    work = [list(value[row]) + list(identity(rows)[row]) for row in range(rows)]
    for column in range(rows):
        pivot = max(range(column, rows), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= tolerance:
            raise ValueError("Cannot invert a singular or ill-conditioned matrix")
        work[column], work[pivot] = work[pivot], work[column]
        pivot_value = work[column][column]
        for inner in range(2 * rows):
            work[column][inner] /= pivot_value
        for row in range(rows):
            if row == column:
                continue
            factor = work[row][column]
            if abs(factor) <= tolerance:
                continue
            for inner in range(2 * rows):
                work[row][inner] -= factor * work[column][inner]
    return matrix(row[rows:] for row in work)


def _pivot_columns(value: Matrix, *, tolerance: float = 1.0e-10) -> tuple[int, ...]:
    rows, columns = shape(value)
    work = [list(row) for row in value]
    pivot_row = 0
    pivots: list[int] = []
    for column in range(columns):
        pivot = max(
            range(pivot_row, rows),
            key=lambda row: abs(work[row][column]),
            default=None,
        )
        if pivot is None or abs(work[pivot][column]) <= tolerance:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        for inner in range(column, columns):
            work[pivot_row][inner] /= pivot_value
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row][column]
            if abs(factor) <= tolerance:
                continue
            for inner in range(column, columns):
                work[row][inner] -= factor * work[pivot_row][inner]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    return tuple(pivots)


def _select_columns(value: Matrix, indices: Sequence[int]) -> Matrix:
    rows, columns = shape(value)
    if any(index < 0 or index >= columns for index in indices):
        raise ValueError("Column index out of range")
    return matrix(
        tuple(value[row][index] for index in indices)
        for row in range(rows)
    )


def _select_rows(value: Matrix, indices: Sequence[int]) -> Matrix:
    rows, _ = shape(value)
    if any(index < 0 or index >= rows for index in indices):
        raise ValueError("Row index out of range")
    return matrix(value[index] for index in indices)


@dataclass(frozen=True, slots=True)
class ActiveFactorization:
    """Exact rank factorization ``T = C B`` with an invertible active core."""

    pivot_rows: tuple[int, ...]
    pivot_columns: tuple[int, ...]
    column_basis: Matrix
    active_core: Matrix
    right_factor: Matrix
    reconstruction_error: float
    compression_gain_proxy: float

    @property
    def active_rank(self) -> int:
        return len(self.pivot_columns)

    def reconstruct(self) -> Matrix:
        return multiply(self.column_basis, self.right_factor)


def active_factorization(
    transformation: Matrix,
    *,
    tolerance: float = 1.0e-10,
) -> ActiveFactorization:
    """Build an exact CUR-derived rank factorization.

    Independent columns form ``C``. Independent rows of ``C`` select an
    invertible core ``U``. With ``R`` the corresponding rows of ``T``,
    ``T = C U^{-1} R = C B``.
    """

    rows, columns = shape(transformation)
    pivot_columns = _pivot_columns(transformation, tolerance=tolerance)
    active_rank = len(pivot_columns)
    if active_rank == 0:
        zero = zeros(rows, 1)
        right = zeros(1, columns)
        return ActiveFactorization(
            pivot_rows=(),
            pivot_columns=(),
            column_basis=zero,
            active_core=((1.0,),),
            right_factor=right,
            reconstruction_error=0.0,
            compression_gain_proxy=float("inf"),
        )

    column_basis = _select_columns(transformation, pivot_columns)
    pivot_rows = _pivot_columns(transpose(column_basis), tolerance=tolerance)
    if len(pivot_rows) != active_rank:
        raise ArithmeticError("Failed to identify an invertible active core")
    row_basis = _select_rows(transformation, pivot_rows)
    active_core = _select_columns(row_basis, pivot_columns)
    right_factor = multiply(matrix_inverse(active_core), row_basis)
    reconstruction = multiply(column_basis, right_factor)
    residual = relative_reconstruction_error(transformation, reconstruction)

    dense_parameters = rows * columns
    factor_parameters = rows * active_rank + active_rank * columns
    index_parameters = len(pivot_rows) + len(pivot_columns)
    gain = dense_parameters / max(factor_parameters + index_parameters, 1)
    return ActiveFactorization(
        pivot_rows=pivot_rows,
        pivot_columns=pivot_columns,
        column_basis=column_basis,
        active_core=active_core,
        right_factor=right_factor,
        reconstruction_error=residual,
        compression_gain_proxy=gain,
    )


def _spectral_decomposition_symmetric_2x2(
    value: Matrix,
) -> tuple[tuple[float, float], Matrix]:
    if shape(value) != (2, 2):
        raise ValueError("Expected a 2x2 matrix")
    a, b = value[0]
    c, d = value[1]
    if abs(b - c) > 1.0e-9:
        raise ValueError("Expected a symmetric matrix")
    off = 0.5 * (b + c)
    center = 0.5 * (a + d)
    radius = sqrt(max(0.0, (0.5 * (a - d)) ** 2 + off * off))
    first = center + radius
    second = center - radius

    if abs(off) > _EPS:
        raw = (first - d, off)
    elif a >= d:
        raw = (1.0, 0.0)
    else:
        raw = (0.0, 1.0)
    norm = sqrt(raw[0] * raw[0] + raw[1] * raw[1])
    v1 = (raw[0] / norm, raw[1] / norm)
    v2 = (-v1[1], v1[0])
    eigenvectors = ((v1[0], v2[0]), (v1[1], v2[1]))
    return (first, second), eigenvectors


def _spectral_reconstruct_2x2(
    eigenvectors: Matrix,
    eigenvalues: Sequence[float],
) -> Matrix:
    diagonal = ((float(eigenvalues[0]), 0.0), (0.0, float(eigenvalues[1])))
    return multiply(multiply(eigenvectors, diagonal), transpose(eigenvectors))


@dataclass(frozen=True, slots=True)
class PolarLog2D:
    rotation: Matrix
    stretch: Matrix
    rotation_generator: Matrix
    strain_generator: Matrix
    singular_values: tuple[float, float]
    reconstruction_error: float

    def reconstruct(self) -> Matrix:
        return multiply(
            matrix_exponential(self.rotation_generator),
            matrix_exponential(self.strain_generator),
        )


def polar_log_2d(transformation: Matrix) -> PolarLog2D:
    """Return ``T = exp(Omega) exp(E)`` for an invertible 2D map with det > 0."""

    if shape(transformation) != (2, 2):
        raise ValueError("polar_log_2d requires a 2x2 transformation")
    det = determinant(transformation)
    if det <= _EPS:
        raise ValueError(
            "Continuous real polar-log sector requires positive determinant"
        )

    gram = multiply(transpose(transformation), transformation)
    eigenvalues, eigenvectors = _spectral_decomposition_symmetric_2x2(gram)
    if min(eigenvalues) <= _EPS:
        raise ValueError("Transformation is singular or numerically rank deficient")

    singular_values = (sqrt(eigenvalues[0]), sqrt(eigenvalues[1]))
    stretch = _spectral_reconstruct_2x2(eigenvectors, singular_values)
    strain_generator = _spectral_reconstruct_2x2(
        eigenvectors,
        (log(singular_values[0]), log(singular_values[1])),
    )
    rotation = multiply(transformation, matrix_inverse(stretch))
    angle = atan2(rotation[1][0], rotation[0][0])
    rotation_generator = ((0.0, -angle), (angle, 0.0))
    reconstruction = multiply(
        matrix_exponential(rotation_generator),
        matrix_exponential(strain_generator),
    )
    return PolarLog2D(
        rotation=rotation,
        stretch=stretch,
        rotation_generator=rotation_generator,
        strain_generator=strain_generator,
        singular_values=singular_values,
        reconstruction_error=relative_reconstruction_error(
            transformation, reconstruction
        ),
    )


def kronecker_product(left: Matrix, right: Matrix) -> Matrix:
    left_rows, left_columns = shape(left)
    right_rows, right_columns = shape(right)
    return matrix(
        tuple(
            left[i][j] * right[k][l]
            for j in range(left_columns)
            for l in range(right_columns)
        )
        for i in range(left_rows)
        for k in range(right_rows)
    )


def kronecker_sum(left: Matrix, right: Matrix) -> Matrix:
    left_rows, left_columns = shape(left)
    right_rows, right_columns = shape(right)
    if left_rows != left_columns or right_rows != right_columns:
        raise ValueError("Kronecker sum requires square generators")
    return add(
        kronecker_product(left, identity(right_rows)),
        kronecker_product(identity(left_rows), right),
    )


@dataclass(frozen=True, slots=True)
class CommutatorEdge:
    left: str
    right: str
    commutator_norm: float
    normalized_strength: float


def commutator_graph(
    named_generators: Mapping[str, Matrix],
) -> tuple[CommutatorEdge, ...]:
    names = tuple(named_generators)
    edges: list[CommutatorEdge] = []
    for left_index, left_name in enumerate(names):
        left = named_generators[left_name]
        for right_name in names[left_index + 1 :]:
            right = named_generators[right_name]
            bracket_norm = frobenius_norm(commutator(left, right))
            denominator = max(
                frobenius_norm(left) * frobenius_norm(right),
                _EPS,
            )
            edges.append(
                CommutatorEdge(
                    left=left_name,
                    right=right_name,
                    commutator_norm=bracket_norm,
                    normalized_strength=bracket_norm / denominator,
                )
            )
    return tuple(edges)


def magnus_second_order_piecewise(
    generators: Sequence[Matrix],
    *,
    step: float,
) -> Matrix:
    """Second-order Magnus generator for equal piecewise-constant time steps."""

    if not generators:
        raise ValueError("At least one generator is required")
    rows, columns = shape(generators[0])
    if rows != columns:
        raise ValueError("Magnus generators must be square")
    if step <= 0.0:
        raise ValueError("step must be positive")
    if any(shape(generator) != (rows, columns) for generator in generators):
        raise ValueError("All Magnus generators must share one shape")

    omega = zeros(rows, columns)
    for generator in generators:
        omega = add(omega, scale(generator, step))
    for later in range(len(generators)):
        for earlier in range(later):
            omega = add(
                omega,
                scale(
                    commutator(generators[later], generators[earlier]),
                    0.5 * step * step,
                ),
            )
    return omega


@dataclass(frozen=True, slots=True)
class MorphSignature:
    domain_dimension: int
    codomain_dimension: int
    rank: int
    kernel_dimension: int
    cokernel_dimension: int
    determinant_sign: int | None
    invertible: bool


@dataclass(frozen=True, slots=True)
class MorphCodex:
    signature: MorphSignature
    representation: str
    continuous_model: str
    discrete_sector: tuple[str, ...]
    singular_sector: tuple[str, ...]
    branch_ledger: BranchLedger
    invariants: dict[str, float | int]
    residuals: dict[str, float]
    uncertainty: dict[str, float]
    validity: dict[str, str]
    status: str = "prototype"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def morph_signature(transformation: Matrix) -> MorphSignature:
    rows, columns = shape(transformation)
    matrix_rank = rank(transformation)
    determinant_sign: int | None = None
    invertible = False
    if rows == columns:
        det = determinant(transformation)
        determinant_sign = 1 if det > _EPS else -1 if det < -_EPS else 0
        invertible = determinant_sign != 0
    return MorphSignature(
        domain_dimension=columns,
        codomain_dimension=rows,
        rank=matrix_rank,
        kernel_dimension=columns - matrix_rank,
        cokernel_dimension=rows - matrix_rank,
        determinant_sign=determinant_sign,
        invertible=invertible,
    )


def build_morph_codex(
    transformation: Matrix,
    *,
    representation: str = "finite-real-matrix",
    branch_ledger: BranchLedger | None = None,
) -> MorphCodex:
    signature = morph_signature(transformation)
    factor = active_factorization(transformation)
    discrete: list[str] = []
    singular: list[str] = []

    if signature.determinant_sign == -1:
        discrete.append("orientation-reversing")
    elif signature.determinant_sign == 1:
        discrete.append("orientation-preserving")
    if signature.kernel_dimension:
        singular.append("non-trivial-kernel")
    if signature.cokernel_dimension:
        singular.append("non-trivial-cokernel")
    if signature.rank == 0:
        singular.append("zero-map")

    continuous_model = (
        "direct-or-product-log-candidate"
        if signature.invertible and signature.determinant_sign != -1
        else "lifted-or-active-support-factorization"
    )
    invariants: dict[str, float | int] = {
        "rank": signature.rank,
        "frobenius_norm": frobenius_norm(transformation),
    }
    if signature.determinant_sign is not None:
        invariants["determinant"] = determinant(transformation)

    return MorphCodex(
        signature=signature,
        representation=representation,
        continuous_model=continuous_model,
        discrete_sector=tuple(discrete),
        singular_sector=tuple(singular),
        branch_ledger=branch_ledger or BranchLedger(),
        invariants=invariants,
        residuals={
            "active_factorization": factor.reconstruction_error,
        },
        uncertainty={
            "measurement": 0.0,
            "logarithm_branch": 0.0,
            "model": 0.0,
        },
        validity={
            "domain": "finite-dimensional real matrices",
            "warning": (
                "Representation and reconstruction do not by themselves "
                "establish compression, causality, or physical validity."
            ),
        },
    )
