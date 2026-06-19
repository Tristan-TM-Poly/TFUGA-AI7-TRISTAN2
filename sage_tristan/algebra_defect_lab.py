"""AlgebraDefectLab for Ω-MATH-TRISTAN.

Represent a finite-dimensional algebra by structure constants and measure the
Tristan defect coordinates: commutator, associator and norm defect.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

Vector = tuple[float, ...]
StructureConstants = tuple[tuple[tuple[float, ...], ...], ...]


def vector_add(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("vector lengths differ")
    return tuple(x + y for x, y in zip(a, b))


def vector_sub(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("vector lengths differ")
    return tuple(x - y for x, y in zip(a, b))


def scalar_mul(scalar: float, vector: Vector) -> Vector:
    return tuple(scalar * x for x in vector)


def l2_norm(vector: Vector) -> float:
    return sqrt(sum(x * x for x in vector))


@dataclass(frozen=True)
class FiniteDimensionalAlgebra:
    """Finite-dimensional algebra over real coefficients.

    structure_constants[i][j][k] is the coefficient of e_k in e_i * e_j.
    """

    structure_constants: StructureConstants

    def __post_init__(self) -> None:
        dim = len(self.structure_constants)
        if dim == 0:
            raise ValueError("algebra dimension must be positive")
        for row in self.structure_constants:
            if len(row) != dim:
                raise ValueError("structure constants must be dim x dim x dim")
            for product in row:
                if len(product) != dim:
                    raise ValueError("structure constants must be dim x dim x dim")

    @property
    def dim(self) -> int:
        return len(self.structure_constants)

    def basis_vector(self, index: int) -> Vector:
        if index < 0 or index >= self.dim:
            raise IndexError("basis index out of range")
        return tuple(1.0 if i == index else 0.0 for i in range(self.dim))

    def multiply(self, x: Vector, y: Vector) -> Vector:
        if len(x) != self.dim or len(y) != self.dim:
            raise ValueError("vectors must match algebra dimension")
        result = [0.0] * self.dim
        for i, xi in enumerate(x):
            if xi == 0:
                continue
            for j, yj in enumerate(y):
                if yj == 0:
                    continue
                product = self.structure_constants[i][j]
                for k, coeff in enumerate(product):
                    result[k] += xi * yj * coeff
        return tuple(result)

    def commutator(self, x: Vector, y: Vector) -> Vector:
        return vector_sub(self.multiply(x, y), self.multiply(y, x))

    def associator(self, x: Vector, y: Vector, z: Vector) -> Vector:
        left = self.multiply(self.multiply(x, y), z)
        right = self.multiply(x, self.multiply(y, z))
        return vector_sub(left, right)

    def norm_defect(self, x: Vector, y: Vector) -> float:
        return l2_norm(self.multiply(x, y)) - l2_norm(x) * l2_norm(y)

    def defect_summary(self, x: Vector, y: Vector, z: Vector | None = None) -> dict[str, float]:
        if z is None:
            z = x
        comm = self.commutator(x, y)
        assoc = self.associator(x, y, z)
        return {
            "commutator_norm": l2_norm(comm),
            "associator_norm": l2_norm(assoc),
            "norm_defect": self.norm_defect(x, y),
        }

    def is_commutative_on_basis(self, *, tolerance: float = 1e-12) -> bool:
        for i in range(self.dim):
            for j in range(self.dim):
                if l2_norm(self.commutator(self.basis_vector(i), self.basis_vector(j))) > tolerance:
                    return False
        return True

    def is_associative_on_basis(self, *, tolerance: float = 1e-12) -> bool:
        for i in range(self.dim):
            for j in range(self.dim):
                for k in range(self.dim):
                    assoc = self.associator(self.basis_vector(i), self.basis_vector(j), self.basis_vector(k))
                    if l2_norm(assoc) > tolerance:
                        return False
        return True


def complex_numbers_as_real_algebra() -> FiniteDimensionalAlgebra:
    """Return R^2 with multiplication equivalent to complex numbers.

    Basis: e0 = 1, e1 = i.  i*i = -1.
    """
    return FiniteDimensionalAlgebra(
        structure_constants=(
            ((1.0, 0.0), (0.0, 1.0)),
            ((0.0, 1.0), (-1.0, 0.0)),
        )
    )


def dual_numbers_as_real_algebra() -> FiniteDimensionalAlgebra:
    """Return R[ε]/(ε^2), a commutative algebra with nilpotent residue."""
    return FiniteDimensionalAlgebra(
        structure_constants=(
            ((1.0, 0.0), (0.0, 1.0)),
            ((0.0, 1.0), (0.0, 0.0)),
        )
    )


def exterior_two_basis_algebra() -> FiniteDimensionalAlgebra:
    """Return a tiny anti-commutative exterior-like algebra on one generator.

    Basis: e0 = 1, e1 = a. Multiplication is associative and a*a = 0.
    This is useful as a nilpotent comparison object.
    """
    return dual_numbers_as_real_algebra()


def aggregate_defects(algebra: FiniteDimensionalAlgebra, vectors: Iterable[Vector]) -> dict[str, float]:
    """Aggregate basis-like sampled defect magnitudes over provided vectors."""
    sample = tuple(vectors)
    if not sample:
        raise ValueError("at least one vector is required")
    comm_total = 0.0
    assoc_total = 0.0
    norm_total = 0.0
    count = 0
    for x in sample:
        for y in sample:
            for z in sample:
                comm_total += l2_norm(algebra.commutator(x, y))
                assoc_total += l2_norm(algebra.associator(x, y, z))
                norm_total += abs(algebra.norm_defect(x, y))
                count += 1
    return {
        "mean_commutator_norm": comm_total / count,
        "mean_associator_norm": assoc_total / count,
        "mean_abs_norm_defect": norm_total / count,
    }
