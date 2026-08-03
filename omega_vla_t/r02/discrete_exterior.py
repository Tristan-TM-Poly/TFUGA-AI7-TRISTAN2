"""Finite chain-complex and discrete Hodge fixtures for Ω-VLA R0.2-MAX."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np
import numpy.typing as npt


RealArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class ChainComplexAudit:
    dimensions: tuple[int, ...]
    boundary_squared_residuals: tuple[float, ...]
    valid: bool
    tolerance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscreteHodgeReport:
    degree: int
    exact: tuple[float, ...]
    coexact: tuple[float, ...]
    harmonic: tuple[float, ...]
    reconstruction_error: float
    exact_coexact_inner_product: float
    harmonic_laplacian_residual: float
    betti_number: int
    theorem_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FiniteChainComplex:
    """A finite real chain complex defined by boundary matrices B_k.

    ``boundaries[k-1]`` represents ``B_k : C_k -> C_{k-1}``.
    The implementation validates ``B_k @ B_{k+1} = 0`` numerically.
    """

    def __init__(
        self,
        boundaries: Sequence[npt.ArrayLike],
        *,
        tolerance: float = 1e-10,
    ) -> None:
        if tolerance <= 0.0:
            raise ValueError("tolerance must be positive")
        self.boundaries = tuple(
            np.asarray(boundary, dtype=float) for boundary in boundaries
        )
        self.tolerance = float(tolerance)
        for degree, boundary in enumerate(self.boundaries, start=1):
            if boundary.ndim != 2:
                raise ValueError(f"B_{degree} must be a matrix")
            if not np.all(np.isfinite(boundary)):
                raise ValueError(f"B_{degree} entries must be finite")
        for degree in range(1, len(self.boundaries)):
            lower = self.boundaries[degree - 1]
            upper = self.boundaries[degree]
            if lower.shape[1] != upper.shape[0]:
                raise ValueError(
                    f"B_{degree} and B_{degree + 1} have incompatible shapes"
                )
        audit = self.audit()
        if not audit.valid:
            raise ValueError("boundary-of-boundary residual exceeds tolerance")

    @property
    def max_degree(self) -> int:
        return len(self.boundaries)

    @property
    def dimensions(self) -> tuple[int, ...]:
        if not self.boundaries:
            return ()
        return (self.boundaries[0].shape[0],) + tuple(
            boundary.shape[1] for boundary in self.boundaries
        )

    def boundary(self, degree: int) -> RealArray:
        if degree < 1 or degree > self.max_degree:
            raise IndexError("boundary degree out of range")
        return self.boundaries[degree - 1]

    def coboundary(self, degree: int) -> RealArray:
        """Return d_degree : C^degree -> C^(degree+1)."""

        if degree < 0 or degree >= self.max_degree:
            raise IndexError("coboundary degree out of range")
        return self.boundaries[degree].T

    def audit(self) -> ChainComplexAudit:
        residuals: list[float] = []
        for degree in range(len(self.boundaries) - 1):
            product = self.boundaries[degree] @ self.boundaries[degree + 1]
            residuals.append(float(np.linalg.norm(product)))
        return ChainComplexAudit(
            dimensions=self.dimensions,
            boundary_squared_residuals=tuple(residuals),
            valid=all(value <= self.tolerance for value in residuals),
            tolerance=self.tolerance,
        )

    def hodge_laplacian(self, degree: int) -> RealArray:
        dimensions = self.dimensions
        if degree < 0 or degree >= len(dimensions):
            raise IndexError("Hodge degree out of range")
        n = dimensions[degree]
        result = np.zeros((n, n), dtype=float)
        if degree >= 1:
            lower = self.boundary(degree)
            result += lower.T @ lower
        if degree < self.max_degree:
            upper = self.boundary(degree + 1)
            result += upper @ upper.T
        return result

    def betti_number(self, degree: int) -> int:
        dimensions = self.dimensions
        if degree < 0 or degree >= len(dimensions):
            raise IndexError("Betti degree out of range")
        rank_lower = (
            int(np.linalg.matrix_rank(self.boundary(degree)))
            if degree >= 1
            else 0
        )
        rank_upper = (
            int(np.linalg.matrix_rank(self.boundary(degree + 1)))
            if degree < self.max_degree
            else 0
        )
        value = dimensions[degree] - rank_lower - rank_upper
        return max(int(value), 0)

    def hodge_decomposition(
        self,
        degree: int,
        cochain: npt.ArrayLike,
    ) -> DiscreteHodgeReport:
        dimensions = self.dimensions
        if degree < 0 or degree >= len(dimensions):
            raise IndexError("Hodge degree out of range")
        vector = np.asarray(cochain, dtype=float).reshape(-1)
        if vector.shape != (dimensions[degree],):
            raise ValueError("cochain dimension does not match chain complex")

        exact = np.zeros_like(vector)
        if degree >= 1:
            exact_basis = self.boundary(degree).T
            coefficients = np.linalg.lstsq(exact_basis, vector, rcond=None)[0]
            exact = exact_basis @ coefficients

        residual_after_exact = vector - exact
        coexact = np.zeros_like(vector)
        if degree < self.max_degree:
            coexact_basis = self.boundary(degree + 1)
            coefficients = np.linalg.lstsq(
                coexact_basis,
                residual_after_exact,
                rcond=None,
            )[0]
            coexact = coexact_basis @ coefficients

        harmonic = vector - exact - coexact
        reconstructed = exact + coexact + harmonic
        laplacian = self.hodge_laplacian(degree)
        return DiscreteHodgeReport(
            degree=degree,
            exact=tuple(float(value) for value in exact),
            coexact=tuple(float(value) for value in coexact),
            harmonic=tuple(float(value) for value in harmonic),
            reconstruction_error=float(np.linalg.norm(vector - reconstructed)),
            exact_coexact_inner_product=float(np.dot(exact, coexact)),
            harmonic_laplacian_residual=float(np.linalg.norm(laplacian @ harmonic)),
            betti_number=self.betti_number(degree),
        )


def oriented_cycle_incidence(vertices: int) -> RealArray:
    """Create B_1 for one consistently oriented cycle graph."""

    if vertices < 3:
        raise ValueError("a cycle requires at least three vertices")
    incidence = np.zeros((vertices, vertices), dtype=float)
    for edge in range(vertices):
        tail = edge
        head = (edge + 1) % vertices
        incidence[tail, edge] = -1.0
        incidence[head, edge] = 1.0
    return incidence


def filled_oriented_triangle() -> FiniteChainComplex:
    """Return the chain complex of one filled oriented 2-simplex."""

    boundary_1 = np.array(
        [
            [-1.0, 0.0, 1.0],
            [1.0, -1.0, 0.0],
            [0.0, 1.0, -1.0],
        ]
    )
    boundary_2 = np.ones((3, 1), dtype=float)
    return FiniteChainComplex((boundary_1, boundary_2))
