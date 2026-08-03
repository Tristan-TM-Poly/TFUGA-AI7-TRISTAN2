"""Dependency-light CSR sparse matrices and operators for Ω-VLA Wave 2.

This module provides deterministic reference semantics without requiring SciPy.
It is intended for fixtures, serialization and bounded baselines, not as a
replacement for mature sparse numerical libraries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Sequence

import numpy as np
import numpy.typing as npt

from ..types import MathType, ScalarSystem, UnitDimension
from .matrix_free import MatrixFreeOperator

Array = npt.NDArray[np.complex128]


class SparseError(ValueError):
    pass


@dataclass(frozen=True)
class CSRMatrix:
    data: tuple[complex, ...]
    indices: tuple[int, ...]
    indptr: tuple[int, ...]
    shape: tuple[int, int]

    def __post_init__(self) -> None:
        rows, columns = self.shape
        if rows < 0 or columns < 0:
            raise SparseError("CSR dimensions cannot be negative")
        if len(self.data) != len(self.indices):
            raise SparseError("CSR data and indices lengths differ")
        if len(self.indptr) != rows + 1:
            raise SparseError("CSR indptr length must equal rows + 1")
        if not self.indptr or self.indptr[0] != 0 or self.indptr[-1] != len(self.data):
            raise SparseError("CSR indptr endpoints are invalid")
        if any(a > b for a, b in zip(self.indptr, self.indptr[1:])):
            raise SparseError("CSR indptr must be nondecreasing")
        if any(index < 0 or index >= columns for index in self.indices):
            raise SparseError("CSR column index out of range")
        for row in range(rows):
            start, stop = self.indptr[row], self.indptr[row + 1]
            row_indices = self.indices[start:stop]
            if tuple(sorted(row_indices)) != row_indices:
                raise SparseError("CSR column indices must be sorted within each row")
            if len(set(row_indices)) != len(row_indices):
                raise SparseError("CSR duplicate column indices are not canonical")
        if any(not np.isfinite(value.real) or not np.isfinite(value.imag) for value in self.data):
            raise SparseError("CSR values must be finite")

    @property
    def nnz(self) -> int:
        return len(self.data)

    @property
    def density(self) -> float:
        size = self.shape[0] * self.shape[1]
        return 0.0 if size == 0 else self.nnz / size

    @classmethod
    def from_dense(cls, matrix: npt.ArrayLike, *, tolerance: float = 0.0) -> "CSRMatrix":
        array = np.asarray(matrix, dtype=np.complex128)
        if array.ndim != 2 or not np.all(np.isfinite(array)):
            raise SparseError("dense source must be a finite matrix")
        if tolerance < 0:
            raise SparseError("tolerance cannot be negative")
        data: list[complex] = []
        indices: list[int] = []
        indptr = [0]
        for row in array:
            for column, value in enumerate(row):
                if abs(value) > tolerance:
                    data.append(complex(value))
                    indices.append(column)
            indptr.append(len(data))
        return cls(tuple(data), tuple(indices), tuple(indptr), tuple(array.shape))

    @classmethod
    def from_coo(
        cls,
        rows: int,
        columns: int,
        entries: Iterable[tuple[int, int, complex | float | int]],
        *,
        drop_tolerance: float = 0.0,
    ) -> "CSRMatrix":
        if rows < 0 or columns < 0:
            raise SparseError("COO dimensions cannot be negative")
        accumulated: dict[tuple[int, int], complex] = {}
        for row, column, value in entries:
            if not (0 <= row < rows and 0 <= column < columns):
                raise SparseError("COO coordinate out of range")
            key = (int(row), int(column))
            accumulated[key] = accumulated.get(key, 0.0j) + complex(value)
        canonical = [
            (row, column, value)
            for (row, column), value in sorted(accumulated.items())
            if abs(value) > drop_tolerance
        ]
        data: list[complex] = []
        indices: list[int] = []
        indptr = [0]
        cursor = 0
        for row in range(rows):
            while cursor < len(canonical) and canonical[cursor][0] == row:
                _, column, value = canonical[cursor]
                data.append(value)
                indices.append(column)
                cursor += 1
            indptr.append(len(data))
        return cls(tuple(data), tuple(indices), tuple(indptr), (rows, columns))

    @classmethod
    def identity(cls, dimension: int) -> "CSRMatrix":
        if dimension < 0:
            raise SparseError("dimension cannot be negative")
        return cls(
            data=tuple(1.0 + 0.0j for _ in range(dimension)),
            indices=tuple(range(dimension)),
            indptr=tuple(range(dimension + 1)),
            shape=(dimension, dimension),
        )

    @classmethod
    def diagonal(cls, diagonal: Sequence[complex | float | int]) -> "CSRMatrix":
        entries = [(index, index, value) for index, value in enumerate(diagonal)]
        return cls.from_coo(len(diagonal), len(diagonal), entries)

    @classmethod
    def laplacian_1d(cls, dimension: int, *, boundary: str = "dirichlet") -> "CSRMatrix":
        if dimension <= 0:
            raise SparseError("dimension must be positive")
        if boundary not in {"dirichlet", "periodic", "neumann"}:
            raise SparseError("unsupported boundary condition")
        entries: list[tuple[int, int, complex]] = []
        for index in range(dimension):
            diagonal = 2.0
            if boundary == "neumann" and index in {0, dimension - 1}:
                diagonal = 1.0
            entries.append((index, index, diagonal))
            if index > 0:
                entries.append((index, index - 1, -1.0))
            if index + 1 < dimension:
                entries.append((index, index + 1, -1.0))
        if boundary == "periodic" and dimension > 1:
            entries.extend([(0, dimension - 1, -1.0), (dimension - 1, 0, -1.0)])
        return cls.from_coo(dimension, dimension, entries)

    def to_dense(self, *, max_elements: int = 4_000_000) -> Array:
        rows, columns = self.shape
        if rows * columns > max_elements:
            raise SparseError("dense conversion exceeds max_elements")
        result = np.zeros(self.shape, dtype=np.complex128)
        for row in range(rows):
            for cursor in range(self.indptr[row], self.indptr[row + 1]):
                result[row, self.indices[cursor]] = self.data[cursor]
        return result

    def matvec(self, vector: npt.ArrayLike) -> Array:
        x = np.asarray(vector, dtype=np.complex128)
        if x.shape != (self.shape[1],):
            raise SparseError(f"matvec expected {(self.shape[1],)}, got {x.shape}")
        result = np.zeros(self.shape[0], dtype=np.complex128)
        for row in range(self.shape[0]):
            total = 0.0j
            for cursor in range(self.indptr[row], self.indptr[row + 1]):
                total += self.data[cursor] * x[self.indices[cursor]]
            result[row] = total
        return result

    def transpose(self, *, conjugate: bool = False) -> "CSRMatrix":
        entries: list[tuple[int, int, complex]] = []
        for row in range(self.shape[0]):
            for cursor in range(self.indptr[row], self.indptr[row + 1]):
                value = self.data[cursor].conjugate() if conjugate else self.data[cursor]
                entries.append((self.indices[cursor], row, value))
        return CSRMatrix.from_coo(self.shape[1], self.shape[0], entries)

    def adjoint(self) -> "CSRMatrix":
        return self.transpose(conjugate=True)

    def add(self, other: "CSRMatrix", *, drop_tolerance: float = 0.0) -> "CSRMatrix":
        if self.shape != other.shape:
            raise SparseError("sparse addition requires matching shapes")
        entries: list[tuple[int, int, complex]] = []
        for matrix in (self, other):
            for row in range(matrix.shape[0]):
                for cursor in range(matrix.indptr[row], matrix.indptr[row + 1]):
                    entries.append((row, matrix.indices[cursor], matrix.data[cursor]))
        return CSRMatrix.from_coo(*self.shape, entries, drop_tolerance=drop_tolerance)

    def scale(self, scalar: complex | float | int, *, drop_tolerance: float = 0.0) -> "CSRMatrix":
        value = complex(scalar)
        entries = []
        for row in range(self.shape[0]):
            for cursor in range(self.indptr[row], self.indptr[row + 1]):
                scaled = value * self.data[cursor]
                if abs(scaled) > drop_tolerance:
                    entries.append((row, self.indices[cursor], scaled))
        return CSRMatrix.from_coo(*self.shape, entries)

    def matmul(self, other: "CSRMatrix", *, max_products: int = 20_000_000, drop_tolerance: float = 0.0) -> "CSRMatrix":
        if self.shape[1] != other.shape[0]:
            raise SparseError("sparse multiplication has incompatible shapes")
        estimated = max(1, self.nnz) * max(1, other.nnz)
        if estimated > max_products:
            raise SparseError("sparse multiplication exceeds max_products envelope")
        other_rows: list[dict[int, complex]] = []
        for row in range(other.shape[0]):
            other_rows.append({
                other.indices[cursor]: other.data[cursor]
                for cursor in range(other.indptr[row], other.indptr[row + 1])
            })
        entries: list[tuple[int, int, complex]] = []
        for row in range(self.shape[0]):
            accumulator: dict[int, complex] = {}
            for cursor in range(self.indptr[row], self.indptr[row + 1]):
                inner = self.indices[cursor]
                left_value = self.data[cursor]
                for column, right_value in other_rows[inner].items():
                    accumulator[column] = accumulator.get(column, 0.0j) + left_value * right_value
            for column, value in sorted(accumulator.items()):
                if abs(value) > drop_tolerance:
                    entries.append((row, column, value))
        return CSRMatrix.from_coo(self.shape[0], other.shape[1], entries)

    def kronecker(self, other: "CSRMatrix", *, max_nnz: int = 20_000_000) -> "CSRMatrix":
        projected_nnz = self.nnz * other.nnz
        if projected_nnz > max_nnz:
            raise SparseError("Kronecker product exceeds max_nnz envelope")
        entries: list[tuple[int, int, complex]] = []
        for left_row in range(self.shape[0]):
            for left_cursor in range(self.indptr[left_row], self.indptr[left_row + 1]):
                left_column = self.indices[left_cursor]
                left_value = self.data[left_cursor]
                for right_row in range(other.shape[0]):
                    for right_cursor in range(other.indptr[right_row], other.indptr[right_row + 1]):
                        row = left_row * other.shape[0] + right_row
                        column = left_column * other.shape[1] + other.indices[right_cursor]
                        entries.append((row, column, left_value * other.data[right_cursor]))
        return CSRMatrix.from_coo(
            self.shape[0] * other.shape[0],
            self.shape[1] * other.shape[1],
            entries,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "shape": list(self.shape),
            "data": [{"real": value.real, "imag": value.imag} for value in self.data],
            "indices": list(self.indices),
            "indptr": list(self.indptr),
            "nnz": self.nnz,
            "density": self.density,
        }

    def digest(self) -> str:
        text = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SparseOperator:
    name: str
    matrix: CSRMatrix
    scalar_system: ScalarSystem = ScalarSystem.COMPLEX
    units: UnitDimension = UnitDimension()
    domain_id: str | None = None
    codomain_id: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SparseError("sparse operators require a name")

    @property
    def math_type(self) -> MathType:
        return MathType.linear_operator(
            self.matrix.shape[0],
            self.matrix.shape[1],
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.domain_id,
            codomain_id=self.codomain_id,
        )

    def apply(self, vector: npt.ArrayLike) -> Array:
        return self.matrix.matvec(vector)

    def adjoint(self) -> "SparseOperator":
        return SparseOperator(
            name=f"adjoint({self.name})",
            matrix=self.matrix.adjoint(),
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.codomain_id,
            codomain_id=self.domain_id,
            tags=tuple(sorted(set(self.tags + ("adjoint",)))),
        )

    def to_matrix_free(self) -> MatrixFreeOperator:
        adjoint = self.matrix.adjoint()
        return MatrixFreeOperator(
            name=self.name,
            codomain_dimension=self.matrix.shape[0],
            domain_dimension=self.matrix.shape[1],
            matvec=self.matrix.matvec,
            rmatvec=adjoint.matvec,
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.domain_id,
            codomain_id=self.codomain_id,
            tags=tuple(sorted(set(self.tags + ("csr",)))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "matrix": self.matrix.canonical_dict(),
            "math_type": self.math_type.to_dict(),
            "tags": list(self.tags),
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        }
