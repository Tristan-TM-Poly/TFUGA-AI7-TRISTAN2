"""Dependency-free linear algebra helpers for Ω-TENSOR-REPAIR-T.

The package deliberately keeps its executable R0.1 kernel in the Python standard
library. Objects are immutable tuples whenever practical, which makes receipts
stable and easy to hash.
"""

from __future__ import annotations

from math import sqrt
from typing import Iterable, Sequence

Vector = tuple[float, ...]
Matrix = tuple[Vector, ...]


def as_vector(values: Iterable[float]) -> Vector:
    return tuple(float(value) for value in values)


def as_matrix(rows: Iterable[Iterable[float]]) -> Matrix:
    matrix = tuple(as_vector(row) for row in rows)
    if not matrix:
        return tuple()
    width = len(matrix[0])
    if width == 0 or any(len(row) != width for row in matrix):
        raise ValueError("matrix rows must be non-empty and rectangular")
    return matrix


def shape(matrix: Matrix) -> tuple[int, int]:
    return (len(matrix), len(matrix[0]) if matrix else 0)


def zeros(rows: int, cols: int) -> Matrix:
    if rows < 0 or cols < 0:
        raise ValueError("matrix dimensions must be non-negative")
    return tuple(tuple(0.0 for _ in range(cols)) for _ in range(rows))


def identity(size: int) -> Matrix:
    if size < 0:
        raise ValueError("identity size must be non-negative")
    return tuple(
        tuple(1.0 if row == col else 0.0 for col in range(size))
        for row in range(size)
    )


def transpose(matrix: Matrix) -> Matrix:
    rows, cols = shape(matrix)
    return tuple(tuple(matrix[row][col] for row in range(rows)) for col in range(cols))


def add(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("matrix shapes must match")
    return tuple(
        tuple(a + b for a, b in zip(left_row, right_row, strict=True))
        for left_row, right_row in zip(left, right, strict=True)
    )


def subtract(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("matrix shapes must match")
    return tuple(
        tuple(a - b for a, b in zip(left_row, right_row, strict=True))
        for left_row, right_row in zip(left, right, strict=True)
    )


def scale(matrix: Matrix, scalar: float) -> Matrix:
    factor = float(scalar)
    return tuple(tuple(factor * value for value in row) for row in matrix)


def matmul(left: Matrix, right: Matrix) -> Matrix:
    left_rows, left_cols = shape(left)
    right_rows, right_cols = shape(right)
    if left_cols != right_rows:
        raise ValueError("incompatible matrix shapes")
    right_t = transpose(right)
    return tuple(
        tuple(dot(left[row], right_t[col]) for col in range(right_cols))
        for row in range(left_rows)
    )


def matvec(matrix: Matrix, vector: Sequence[float]) -> Vector:
    _, cols = shape(matrix)
    if cols != len(vector):
        raise ValueError("incompatible matrix and vector shapes")
    return tuple(dot(row, vector) for row in matrix)


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector dimensions must match")
    return sum(float(a) * float(b) for a, b in zip(left, right, strict=True))


def norm(vector: Sequence[float]) -> float:
    return sqrt(dot(vector, vector))


def frobenius_norm(matrix: Matrix) -> float:
    return sqrt(sum(value * value for row in matrix for value in row))


def trace(matrix: Matrix) -> float:
    rows, cols = shape(matrix)
    if rows != cols:
        raise ValueError("trace requires a square matrix")
    return sum(matrix[index][index] for index in range(rows))


def flatten(matrix: Matrix) -> Vector:
    return tuple(value for row in matrix for value in row)


def unflatten(vector: Sequence[float], rows: int, cols: int) -> Matrix:
    if rows * cols != len(vector):
        raise ValueError("vector length does not match requested matrix shape")
    values = tuple(float(value) for value in vector)
    return tuple(values[row * cols : (row + 1) * cols] for row in range(rows))


def outer(left: Sequence[float], right: Sequence[float]) -> Matrix:
    return tuple(tuple(float(a) * float(b) for b in right) for a in left)


def normalize(vector: Sequence[float], *, epsilon: float = 1e-15) -> Vector:
    length = norm(vector)
    if length <= epsilon:
        raise ValueError("cannot normalize a near-zero vector")
    return tuple(float(value) / length for value in vector)


def max_abs(matrix: Matrix) -> float:
    return max((abs(value) for row in matrix for value in row), default=0.0)


def almost_equal(left: Matrix, right: Matrix, *, tolerance: float = 1e-10) -> bool:
    if shape(left) != shape(right):
        return False
    return max_abs(subtract(left, right)) <= tolerance


def block_extract(
    matrix: Matrix,
    row_start: int,
    row_stop: int,
    col_start: int,
    col_stop: int,
) -> Matrix:
    rows, cols = shape(matrix)
    if not (0 <= row_start <= row_stop <= rows and 0 <= col_start <= col_stop <= cols):
        raise ValueError("invalid block bounds")
    return tuple(tuple(row[col_start:col_stop]) for row in matrix[row_start:row_stop])


def block_insert(base: Matrix, block: Matrix, row_start: int, col_start: int) -> Matrix:
    rows, cols = shape(base)
    block_rows, block_cols = shape(block)
    if row_start < 0 or col_start < 0 or row_start + block_rows > rows or col_start + block_cols > cols:
        raise ValueError("block does not fit in base matrix")
    mutable = [list(row) for row in base]
    for row in range(block_rows):
        for col in range(block_cols):
            mutable[row_start + row][col_start + col] = block[row][col]
    return as_matrix(mutable)
