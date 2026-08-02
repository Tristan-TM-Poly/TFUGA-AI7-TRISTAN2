"""OAK-safe logarithmic/exponential morphism kernel for Ω-LOGEXP-MORPH-T∞.

The module separates four claims that are often conflated:

1. direct exponentiation: an invertible endomorphism may be ``exp(L)``;
2. ordered products: a transformation may require several exponentials;
3. lifted exponentiation: arbitrary linear maps can be encoded in a larger
   invertible block operator;
4. compression: a logarithm is only a useful compressed genome when it admits
   a shorter, stable, reconstructive representation in a chosen basis.

Only finite-dimensional real matrices are implemented here.  Matrix logarithms
use a Mercator series and therefore require a matrix sufficiently close to the
identity.  This deliberate limitation keeps failure modes explicit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, log2
from typing import Iterable, Sequence, TypeAlias

Matrix: TypeAlias = tuple[tuple[float, ...], ...]

_EPS = 1.0e-12


def matrix(rows: Iterable[Iterable[float]]) -> Matrix:
    converted = tuple(tuple(float(value) for value in row) for row in rows)
    if not converted:
        raise ValueError("A matrix must contain at least one row")
    width = len(converted[0])
    if width == 0 or any(len(row) != width for row in converted):
        raise ValueError("Matrix rows must have one common non-zero width")
    return converted


def shape(value: Matrix) -> tuple[int, int]:
    return len(value), len(value[0])


def require_square(value: Matrix) -> int:
    rows, columns = shape(value)
    if rows != columns:
        raise ValueError(f"Expected a square matrix, got {rows}x{columns}")
    return rows


def zeros(rows: int, columns: int) -> Matrix:
    if rows <= 0 or columns <= 0:
        raise ValueError("Matrix dimensions must be positive")
    return tuple(tuple(0.0 for _ in range(columns)) for _ in range(rows))


def identity(size: int) -> Matrix:
    if size <= 0:
        raise ValueError("Identity size must be positive")
    return tuple(
        tuple(1.0 if row == column else 0.0 for column in range(size))
        for row in range(size)
    )


def add(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("Cannot add matrices with different shapes")
    rows, columns = shape(left)
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(columns))
        for row in range(rows)
    )


def subtract(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("Cannot subtract matrices with different shapes")
    rows, columns = shape(left)
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(columns))
        for row in range(rows)
    )


def scale(value: Matrix, scalar: float) -> Matrix:
    return tuple(tuple(float(scalar) * entry for entry in row) for row in value)


def transpose(value: Matrix) -> Matrix:
    rows, columns = shape(value)
    return tuple(
        tuple(value[row][column] for row in range(rows))
        for column in range(columns)
    )


def multiply(left: Matrix, right: Matrix) -> Matrix:
    left_rows, left_columns = shape(left)
    right_rows, right_columns = shape(right)
    if left_columns != right_rows:
        raise ValueError(
            f"Incompatible multiplication shapes: "
            f"{left_rows}x{left_columns} and {right_rows}x{right_columns}"
        )
    right_t = transpose(right)
    return tuple(
        tuple(sum(a * b for a, b in zip(row, column)) for column in right_t)
        for row in left
    )


def matrix_vector_multiply(value: Matrix, vector: Sequence[float]) -> tuple[float, ...]:
    rows, columns = shape(value)
    if len(vector) != columns:
        raise ValueError(f"Expected vector length {columns}, got {len(vector)}")
    return tuple(
        sum(value[row][column] * float(vector[column]) for column in range(columns))
        for row in range(rows)
    )


def trace(value: Matrix) -> float:
    size = require_square(value)
    return sum(value[index][index] for index in range(size))


def max_row_sum_norm(value: Matrix) -> float:
    return max(sum(abs(entry) for entry in row) for row in value)


def frobenius_norm(value: Matrix) -> float:
    return sum(entry * entry for row in value for entry in row) ** 0.5


def determinant(value: Matrix) -> float:
    size = require_square(value)
    work = [list(row) for row in value]
    result = 1.0
    sign = 1.0
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= _EPS:
            return 0.0
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign *= -1.0
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, size):
            factor = work[row][column] / pivot_value
            for inner in range(column + 1, size):
                work[row][inner] -= factor * work[column][inner]
    return sign * result


def rank(value: Matrix, tolerance: float = 1.0e-10) -> int:
    rows, columns = shape(value)
    work = [list(row) for row in value]
    pivot_row = 0
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
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def matrix_exponential(
    generator: Matrix,
    *,
    tolerance: float = 1.0e-14,
    max_terms: int = 96,
) -> Matrix:
    """Return ``exp(generator)`` using scaling, Taylor summation, and squaring."""

    size = require_square(generator)
    norm = max_row_sum_norm(generator)
    squarings = max(0, int(ceil(log2(norm / 0.5)))) if norm > 0.5 else 0
    scaled_generator = scale(generator, 2.0 ** (-squarings))

    result = identity(size)
    term = identity(size)
    for order in range(1, max_terms + 1):
        term = scale(multiply(term, scaled_generator), 1.0 / order)
        result = add(result, term)
        if max_row_sum_norm(term) <= tolerance:
            break
    else:
        raise ArithmeticError("Matrix exponential did not converge within max_terms")

    for _ in range(squarings):
        result = multiply(result, result)
    return result


def matrix_logarithm_near_identity(
    transformation: Matrix,
    *,
    tolerance: float = 1.0e-14,
    max_terms: int = 512,
) -> Matrix:
    """Return a real Mercator logarithm when ``||T-I||_∞ < 1``.

    This is not a global matrix-logarithm routine. It intentionally rejects
    matrices outside the convergence ball rather than silently selecting an
    unstable or complex branch.
    """

    size = require_square(transformation)
    delta = subtract(transformation, identity(size))
    norm = max_row_sum_norm(delta)
    if norm >= 1.0:
        raise ValueError(
            "Mercator logarithm requires ||T-I||_∞ < 1; "
            f"received {norm:.6g}"
        )

    result = zeros(size, size)
    power = identity(size)
    for order in range(1, max_terms + 1):
        power = multiply(power, delta)
        signed = 1.0 if order % 2 == 1 else -1.0
        term = scale(power, signed / order)
        result = add(result, term)
        if max_row_sum_norm(term) <= tolerance:
            break
    else:
        raise ArithmeticError("Matrix logarithm did not converge within max_terms")
    return result


def commutator(left: Matrix, right: Matrix) -> Matrix:
    require_square(left)
    require_square(right)
    if shape(left) != shape(right):
        raise ValueError("Commutator operands must have the same square shape")
    return subtract(multiply(left, right), multiply(right, left))


def bch(left: Matrix, right: Matrix, *, order: int = 4) -> Matrix:
    """Truncated BCH generator for ``exp(left) exp(right)``."""

    if order not in {1, 2, 3, 4}:
        raise ValueError("BCH order must be one of 1, 2, 3, or 4")
    require_square(left)
    require_square(right)
    if shape(left) != shape(right):
        raise ValueError("BCH operands must have the same square shape")

    result = add(left, right)
    if order == 1:
        return result

    ab = commutator(left, right)
    result = add(result, scale(ab, 0.5))
    if order == 2:
        return result

    result = add(result, scale(commutator(left, ab), 1.0 / 12.0))
    result = add(
        result,
        scale(commutator(right, commutator(right, left)), 1.0 / 12.0),
    )
    if order == 3:
        return result

    fourth = commutator(right, commutator(left, ab))
    return add(result, scale(fourth, -1.0 / 24.0))


def ordered_exponential_product(generators: Sequence[Matrix]) -> Matrix:
    if not generators:
        raise ValueError("At least one generator is required")
    size = require_square(generators[0])
    result = identity(size)
    for generator in generators:
        if shape(generator) != (size, size):
            raise ValueError("All generators must share one square shape")
        result = multiply(result, matrix_exponential(generator))
    return result


def effective_generator_near_identity(generators: Sequence[Matrix]) -> Matrix:
    return matrix_logarithm_near_identity(ordered_exponential_product(generators))


def nilpotent_lift(linear_map: Matrix) -> Matrix:
    """Embed ``T: R^n -> R^m`` as ``N_T`` on ``R^n direct-sum R^m``."""

    output_size, input_size = shape(linear_map)
    total = input_size + output_size
    rows = [[0.0 for _ in range(total)] for _ in range(total)]
    for output_index in range(output_size):
        for input_index in range(input_size):
            rows[input_size + output_index][input_index] = linear_map[output_index][input_index]
    return matrix(rows)


def lift_input(vector: Sequence[float], output_size: int) -> tuple[float, ...]:
    if output_size <= 0:
        raise ValueError("Output size must be positive")
    return tuple(float(value) for value in vector) + tuple(0.0 for _ in range(output_size))


def project_lifted_output(
    lifted_vector: Sequence[float],
    *,
    input_size: int,
) -> tuple[float, ...]:
    if input_size < 0 or input_size > len(lifted_vector):
        raise ValueError("Invalid input_size for lifted vector")
    return tuple(float(value) for value in lifted_vector[input_size:])


def homogeneous_affine(linear: Matrix, translation: Sequence[float]) -> Matrix:
    rows, columns = shape(linear)
    if rows != columns:
        raise ValueError("Affine homogeneous representation requires a square linear map")
    if len(translation) != rows:
        raise ValueError(f"Expected translation length {rows}, got {len(translation)}")
    result = [
        [linear[row][column] for column in range(columns)] + [float(translation[row])]
        for row in range(rows)
    ]
    result.append([0.0 for _ in range(columns)] + [1.0])
    return matrix(result)


def semigroup_defect(later: Matrix, earlier_product: Matrix) -> float:
    if shape(later) != shape(earlier_product):
        raise ValueError("Semigroup operands must have the same shape")
    denominator = max(frobenius_norm(later), _EPS)
    return frobenius_norm(subtract(later, earlier_product)) / denominator


def relative_reconstruction_error(target: Matrix, reconstruction: Matrix) -> float:
    if shape(target) != shape(reconstruction):
        raise ValueError("Target and reconstruction must have the same shape")
    return frobenius_norm(subtract(target, reconstruction)) / max(
        frobenius_norm(target), _EPS
    )


def _flatten(value: Matrix) -> tuple[float, ...]:
    return tuple(entry for row in value for entry in row)


def _solve_linear_system(coefficients: list[list[float]], values: list[float]) -> list[float]:
    size = len(values)
    work = [coefficients[row][:] + [values[row]] for row in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= _EPS:
            raise ValueError("Generator basis is linearly dependent or ill-conditioned")
        work[column], work[pivot] = work[pivot], work[column]
        pivot_value = work[column][column]
        for inner in range(column, size + 1):
            work[column][inner] /= pivot_value
        for row in range(size):
            if row == column:
                continue
            factor = work[row][column]
            for inner in range(column, size + 1):
                work[row][inner] -= factor * work[column][inner]
    return [work[row][size] for row in range(size)]


def compress_in_basis(
    target_generator: Matrix,
    basis: Sequence[Matrix],
    *,
    ridge: float = 1.0e-12,
) -> tuple[tuple[float, ...], Matrix, float]:
    """Least-squares projection of a generator onto a finite basis."""

    if not basis:
        raise ValueError("At least one basis generator is required")
    target_shape = shape(target_generator)
    if any(shape(generator) != target_shape for generator in basis):
        raise ValueError("All basis generators must match the target shape")

    columns = [_flatten(generator) for generator in basis]
    target = _flatten(target_generator)
    gram = [
        [
            sum(left * right for left, right in zip(columns[row], columns[column]))
            + (ridge if row == column else 0.0)
            for column in range(len(basis))
        ]
        for row in range(len(basis))
    ]
    rhs = [
        sum(entry * target_entry for entry, target_entry in zip(column, target))
        for column in columns
    ]
    coefficients = tuple(_solve_linear_system(gram, rhs))

    approximation = zeros(*target_shape)
    for coefficient, generator in zip(coefficients, basis):
        approximation = add(approximation, scale(generator, coefficient))
    residual = relative_reconstruction_error(target_generator, approximation)
    return coefficients, approximation, residual


@dataclass(frozen=True, slots=True)
class BranchLedger:
    branch: str = "real-near-identity"
    winding_numbers: tuple[int, ...] = ()
    continuity_verified: bool = False
    distance_to_cut: float | None = None


@dataclass(frozen=True, slots=True)
class MorphSector:
    rows: int
    columns: int
    rank: int
    determinant_sign: int | None
    invertible: bool

    @classmethod
    def classify(cls, transformation: Matrix) -> "MorphSector":
        rows, columns = shape(transformation)
        matrix_rank = rank(transformation)
        if rows == columns:
            value = determinant(transformation)
            determinant_sign = 1 if value > _EPS else -1 if value < -_EPS else 0
            invertible = determinant_sign != 0
        else:
            determinant_sign = None
            invertible = False
        return cls(rows, columns, matrix_rank, determinant_sign, invertible)


@dataclass(frozen=True, slots=True)
class GeneratorGenome:
    generator_names: tuple[str, ...]
    coefficients: tuple[float, ...]
    branch_ledger: BranchLedger
    logarithm_residual: float
    reconstruction_residual: float
    domain: str
    status: str = "prototype"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
