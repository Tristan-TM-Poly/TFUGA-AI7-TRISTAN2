"""Orthonormal irreducible coordinates for real square rank-2 tensors.

The basis realizes the exact decomposition

    M_d(R) = Sym^2_0(R^d) ⊕ R I ⊕ Λ^2(R^d)

with an explicit Frobenius-orthonormal basis in every positive dimension.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Sequence

from .linalg import Matrix, add, as_matrix, frobenius_norm, scale, shape, subtract, zeros


def frobenius_inner(left: Matrix, right: Matrix) -> float:
    if shape(left) != shape(right):
        raise ValueError("matrix shapes must match")
    return sum(
        a * b
        for left_row, right_row in zip(left, right, strict=True)
        for a, b in zip(left_row, right_row, strict=True)
    )


@dataclass(frozen=True)
class BasisElement:
    name: str
    sector: str
    matrix: Matrix

    @property
    def dimension(self) -> int:
        rows, cols = shape(self.matrix)
        if rows != cols:
            raise ValueError("basis element must be square")
        return rows


@dataclass(frozen=True)
class IrreducibleCoordinates:
    size: int
    symmetric_traceless: tuple[float, ...]
    isotropic: tuple[float, ...]
    antisymmetric: tuple[float, ...]
    reconstruction: Matrix
    residual: Matrix
    reconstruction_error: float

    @property
    def full_coordinates(self) -> tuple[float, ...]:
        return self.symmetric_traceless + self.isotropic + self.antisymmetric

    def to_dict(self) -> dict[str, object]:
        return {
            "size": self.size,
            "sector_dimensions": {
                "symmetric_traceless": len(self.symmetric_traceless),
                "isotropic": len(self.isotropic),
                "antisymmetric": len(self.antisymmetric),
            },
            "coordinates": {
                "symmetric_traceless": list(self.symmetric_traceless),
                "isotropic": list(self.isotropic),
                "antisymmetric": list(self.antisymmetric),
            },
            "reconstruction": [list(row) for row in self.reconstruction],
            "residual": [list(row) for row in self.residual],
            "reconstruction_error": self.reconstruction_error,
        }


def _matrix_with_entries(size: int, entries: Iterable[tuple[int, int, float]]) -> Matrix:
    mutable = [[0.0 for _ in range(size)] for _ in range(size)]
    for row, col, value in entries:
        mutable[row][col] = float(value)
    return as_matrix(mutable)


def square_irreducible_basis(size: int) -> tuple[BasisElement, ...]:
    """Return a deterministic Frobenius-orthonormal basis of ``M_size(R)``.

    Ordering is symmetric-traceless diagonal, symmetric-traceless off-diagonal,
    isotropic, then antisymmetric. This makes sector slicing deterministic.
    """

    if size <= 0:
        raise ValueError("size must be positive")
    elements: list[BasisElement] = []

    # Cartan-like traceless diagonal basis.
    for k in range(1, size):
        denominator = sqrt(k * (k + 1))
        entries = [(index, index, 1.0 / denominator) for index in range(k)]
        entries.append((k, k, -k / denominator))
        elements.append(BasisElement(f"sym0_diag_{k}", "symmetric_traceless", _matrix_with_entries(size, entries)))

    # Symmetric off-diagonal basis.
    inv_sqrt_two = 1.0 / sqrt(2.0)
    for row in range(size):
        for col in range(row + 1, size):
            matrix = _matrix_with_entries(
                size,
                ((row, col, inv_sqrt_two), (col, row, inv_sqrt_two)),
            )
            elements.append(BasisElement(f"sym0_off_{row}_{col}", "symmetric_traceless", matrix))

    isotropic = _matrix_with_entries(
        size,
        ((index, index, 1.0 / sqrt(size)) for index in range(size)),
    )
    elements.append(BasisElement("isotropic", "isotropic", isotropic))

    # Antisymmetric basis.
    for row in range(size):
        for col in range(row + 1, size):
            matrix = _matrix_with_entries(
                size,
                ((row, col, inv_sqrt_two), (col, row, -inv_sqrt_two)),
            )
            elements.append(BasisElement(f"anti_{row}_{col}", "antisymmetric", matrix))

    if len(elements) != size * size:
        raise AssertionError("irreducible basis cardinality mismatch")
    return tuple(elements)


def basis_gram_matrix(basis: Sequence[BasisElement]) -> Matrix:
    return tuple(
        tuple(frobenius_inner(left.matrix, right.matrix) for right in basis)
        for left in basis
    )


def basis_orthonormality_error(basis: Sequence[BasisElement]) -> float:
    if not basis:
        return 0.0
    gram = basis_gram_matrix(basis)
    return max(
        abs(value - (1.0 if row == col else 0.0))
        for row, values in enumerate(gram)
        for col, value in enumerate(values)
    )


def coordinates(matrix: Matrix, basis: Sequence[BasisElement]) -> tuple[float, ...]:
    rows, cols = shape(matrix)
    if rows != cols or rows == 0:
        raise ValueError("matrix must be non-empty and square")
    if any(element.dimension != rows for element in basis):
        raise ValueError("basis dimension does not match matrix")
    return tuple(frobenius_inner(matrix, element.matrix) for element in basis)


def reconstruct_from_coordinates(
    values: Sequence[float],
    basis: Sequence[BasisElement],
) -> Matrix:
    if len(values) != len(basis):
        raise ValueError("coordinate count must match basis cardinality")
    if not basis:
        return tuple()
    size = basis[0].dimension
    result = zeros(size, size)
    for value, element in zip(values, basis, strict=True):
        result = add(result, scale(element.matrix, float(value)))
    return result


def analyze_square_irreducible(matrix: Matrix) -> IrreducibleCoordinates:
    rows, cols = shape(matrix)
    if rows != cols or rows == 0:
        raise ValueError("matrix must be non-empty and square")
    basis = square_irreducible_basis(rows)
    values = coordinates(matrix, basis)
    reconstruction = reconstruct_from_coordinates(values, basis)
    residual = subtract(matrix, reconstruction)
    sector_values = {
        sector: tuple(
            value
            for value, element in zip(values, basis, strict=True)
            if element.sector == sector
        )
        for sector in ("symmetric_traceless", "isotropic", "antisymmetric")
    }
    return IrreducibleCoordinates(
        size=rows,
        symmetric_traceless=sector_values["symmetric_traceless"],
        isotropic=sector_values["isotropic"],
        antisymmetric=sector_values["antisymmetric"],
        reconstruction=reconstruction,
        residual=residual,
        reconstruction_error=frobenius_norm(residual),
    )
