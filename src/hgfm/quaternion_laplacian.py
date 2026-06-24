"""Quaternion HGFM Laplacian utilities.

This module gives an executable OAK-4-style numerical check for the theorem:

    L_H = B W B^dagger

with quaternionic incidence B and real non-negative diagonal weights W.

The implementation intentionally avoids third-party dependencies so it can run in the
repository's first CI pass. It is not optimized; it is a correctness seed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Quaternion:
    """Minimal quaternion with Hamilton product."""

    r: float = 0.0
    i: float = 0.0
    j: float = 0.0
    k: float = 0.0

    def __add__(self, other: "Quaternion") -> "Quaternion":
        return Quaternion(self.r + other.r, self.i + other.i, self.j + other.j, self.k + other.k)

    def __sub__(self, other: "Quaternion") -> "Quaternion":
        return Quaternion(self.r - other.r, self.i - other.i, self.j - other.j, self.k - other.k)

    def __neg__(self) -> "Quaternion":
        return Quaternion(-self.r, -self.i, -self.j, -self.k)

    def __mul__(self, other: "Quaternion | float") -> "Quaternion":
        if isinstance(other, (int, float)):
            return Quaternion(self.r * other, self.i * other, self.j * other, self.k * other)
        a, b, c, d = self.r, self.i, self.j, self.k
        e, f, g, h = other.r, other.i, other.j, other.k
        return Quaternion(
            a * e - b * f - c * g - d * h,
            a * f + b * e + c * h - d * g,
            a * g - b * h + c * e + d * f,
            a * h + b * g - c * f + d * e,
        )

    def __rmul__(self, other: float) -> "Quaternion":
        if isinstance(other, (int, float)):
            return self * float(other)
        return NotImplemented

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.r, -self.i, -self.j, -self.k)

    def norm_squared(self) -> float:
        return self.r * self.r + self.i * self.i + self.j * self.j + self.k * self.k

    def is_real(self, tol: float = 1e-9) -> bool:
        return abs(self.i) <= tol and abs(self.j) <= tol and abs(self.k) <= tol

    def almost_equal(self, other: "Quaternion", tol: float = 1e-9) -> bool:
        return (
            isclose(self.r, other.r, abs_tol=tol)
            and isclose(self.i, other.i, abs_tol=tol)
            and isclose(self.j, other.j, abs_tol=tol)
            and isclose(self.k, other.k, abs_tol=tol)
        )


Q0 = Quaternion(0.0, 0.0, 0.0, 0.0)


Matrix = List[List[Quaternion]]
Vector = List[Quaternion]


def q(value: float | Sequence[float] | Quaternion) -> Quaternion:
    """Coerce a scalar, 4-tuple, or Quaternion into a Quaternion."""

    if isinstance(value, Quaternion):
        return value
    if isinstance(value, (int, float)):
        return Quaternion(float(value), 0.0, 0.0, 0.0)
    if len(value) != 4:
        raise ValueError("quaternion sequences must have length 4")
    return Quaternion(float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def zeros(rows: int, cols: int) -> Matrix:
    return [[Q0 for _ in range(cols)] for _ in range(rows)]


def dagger(matrix: Matrix) -> Matrix:
    """Quaternionic conjugate transpose."""

    if not matrix:
        return []
    rows = len(matrix)
    cols = len(matrix[0])
    return [[matrix[r][c].conjugate() for r in range(rows)] for c in range(cols)]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """Matrix multiplication over non-commutative quaternions.

    Order is preserved exactly as sum_k a[i][k] * b[k][j].
    """

    if not a or not b:
        return []
    rows = len(a)
    inner = len(a[0])
    if len(b) != inner:
        raise ValueError("incompatible matrix shapes")
    cols = len(b[0])
    out = zeros(rows, cols)
    for i in range(rows):
        for j in range(cols):
            total = Q0
            for k in range(inner):
                total = total + a[i][k] * b[k][j]
            out[i][j] = total
    return out


def diagonal_real(weights: Iterable[float]) -> Matrix:
    weights_list = [float(w) for w in weights]
    out = zeros(len(weights_list), len(weights_list))
    for idx, weight in enumerate(weights_list):
        if weight < 0:
            raise ValueError("quaternion HGFM Laplacian requires non-negative real weights")
        out[idx][idx] = Quaternion(weight, 0.0, 0.0, 0.0)
    return out


def quaternion_laplacian(incidence: Matrix, weights: Iterable[float]) -> Matrix:
    """Compute L_H = B W B^dagger."""

    weighted = matmul(incidence, diagonal_real(weights))
    return matmul(weighted, dagger(incidence))


def is_hermitian(matrix: Matrix, tol: float = 1e-9) -> bool:
    return all(matrix[i][j].almost_equal(matrix[j][i].conjugate(), tol=tol) for i in range(len(matrix)) for j in range(len(matrix)))


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    if not matrix:
        return []
    if len(matrix[0]) != len(vector):
        raise ValueError("incompatible matrix/vector shapes")
    out: Vector = []
    for row in matrix:
        total = Q0
        for entry, value in zip(row, vector):
            total = total + entry * value
        out.append(total)
    return out


def quadratic_form(vector: Vector, matrix: Matrix) -> Quaternion:
    """Return x^dagger A x as a Quaternion."""

    ax = matvec(matrix, vector)
    total = Q0
    for x_i, ax_i in zip(vector, ax):
        total = total + x_i.conjugate() * ax_i
    return total


def example_incidence() -> Matrix:
    """Small deterministic quaternionic incidence matrix for tests/examples."""

    return [
        [Quaternion(1, 1, 0, 0), Quaternion(0, 1, -1, 0), Quaternion(0, 0, 0, 1)],
        [Quaternion(-1, 0, 1, 0), Quaternion(2, 0, 0, -1), Quaternion(1, -1, 0, 0)],
        [Quaternion(0, 0, 1, 1), Quaternion(-1, 0, 1, 0), Quaternion(2, 0, 0, 0)],
    ]
