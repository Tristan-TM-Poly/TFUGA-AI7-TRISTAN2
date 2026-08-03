"""Core linear-algebra objects for Ω-VLA-T∞ R0.1.

The module deliberately separates abstract objects from coordinates, metrics,
numerical tolerances, and epistemic claims.  It is research software, not a new
mathematical proof system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.float64]


def _as_float_array(value: npt.ArrayLike, *, ndim: int | None = None) -> Array:
    array = np.asarray(value, dtype=float)
    if ndim is not None and array.ndim != ndim:
        raise ValueError(f"Expected an array with ndim={ndim}, got {array.ndim}.")
    if not np.all(np.isfinite(array)):
        raise ValueError("Arrays must contain only finite values.")
    return array


@dataclass(frozen=True)
class VectorSpace:
    """Finite-dimensional real vector space equipped with a declared metric."""

    dimension: int
    metric: Array | None = None
    name: str = "V"
    units: tuple[str, ...] | None = None
    tolerance: float = 1e-12

    def __post_init__(self) -> None:
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")

        metric = np.eye(self.dimension) if self.metric is None else _as_float_array(self.metric, ndim=2)
        if metric.shape != (self.dimension, self.dimension):
            raise ValueError("metric shape must match the vector-space dimension")
        if not np.allclose(metric, metric.T, atol=self.tolerance, rtol=0.0):
            raise ValueError("metric must be symmetric")
        eigenvalues = np.linalg.eigvalsh(metric)
        if float(np.min(eigenvalues)) <= self.tolerance:
            raise ValueError("metric must be positive definite")
        if self.units is not None and len(self.units) != self.dimension:
            raise ValueError("units must contain one entry per coordinate")

        object.__setattr__(self, "metric", metric)

    def vector(self, coordinates: npt.ArrayLike) -> Array:
        vector = _as_float_array(coordinates, ndim=1)
        if vector.shape != (self.dimension,):
            raise ValueError("vector dimension is incompatible with the space")
        return vector

    def inner(self, left: npt.ArrayLike, right: npt.ArrayLike) -> float:
        x = self.vector(left)
        y = self.vector(right)
        assert self.metric is not None
        return float(x @ self.metric @ y)

    def norm(self, vector: npt.ArrayLike) -> float:
        return float(np.sqrt(max(self.inner(vector, vector), 0.0)))

    def covector(self, vector: npt.ArrayLike) -> Array:
        """Lower an index with the declared metric."""
        x = self.vector(vector)
        assert self.metric is not None
        return self.metric @ x

    def raise_index(self, covector: npt.ArrayLike) -> Array:
        covector_array = self.vector(covector)
        assert self.metric is not None
        return np.linalg.solve(self.metric, covector_array)


@dataclass(frozen=True)
class SVDReport:
    singular_values: Array
    exact_rank: int
    threshold_rank: int
    effective_rank: float
    condition_number: float
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "singular_values": self.singular_values.tolist(),
            "exact_rank": self.exact_rank,
            "threshold_rank": self.threshold_rank,
            "effective_rank": self.effective_rank,
            "condition_number": self.condition_number,
            "threshold": self.threshold,
        }


@dataclass
class LinearOperator:
    """Coordinate representation of a linear map between metric spaces."""

    matrix: Array
    domain: VectorSpace
    codomain: VectorSpace
    name: str = "A"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.matrix = _as_float_array(self.matrix, ndim=2)
        expected = (self.codomain.dimension, self.domain.dimension)
        if self.matrix.shape != expected:
            raise ValueError(f"operator shape must be {expected}, got {self.matrix.shape}")

    def apply(self, vector: npt.ArrayLike) -> Array:
        return self.matrix @ self.domain.vector(vector)

    def residual(self, x: npt.ArrayLike, y: npt.ArrayLike) -> Array:
        target = self.codomain.vector(y)
        return target - self.apply(x)

    def residual_norm(self, x: npt.ArrayLike, y: npt.ArrayLike) -> float:
        return self.codomain.norm(self.residual(x, y))

    def kernel_basis(self, *, threshold: float | None = None) -> Array:
        _, singular_values, vh = np.linalg.svd(self.matrix, full_matrices=True)
        if threshold is None:
            scale = singular_values[0] if singular_values.size else 1.0
            threshold = max(self.matrix.shape) * np.finfo(float).eps * scale
        rank = int(np.count_nonzero(singular_values > threshold))
        return vh[rank:].T.copy()

    def svd_report(self, *, threshold: float = 1e-10) -> SVDReport:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        singular_values = np.linalg.svd(self.matrix, compute_uv=False)
        exact_rank = int(np.linalg.matrix_rank(self.matrix))
        threshold_rank = int(np.count_nonzero(singular_values > threshold))
        total = float(np.sum(singular_values))
        if total <= np.finfo(float).tiny:
            effective_rank = 0.0
        else:
            probabilities = singular_values[singular_values > 0] / total
            entropy = -float(np.sum(probabilities * np.log(probabilities)))
            effective_rank = float(np.exp(entropy))
        condition = float(np.linalg.cond(self.matrix))
        return SVDReport(
            singular_values=singular_values,
            exact_rank=exact_rank,
            threshold_rank=threshold_rank,
            effective_rank=effective_rank,
            condition_number=condition,
            threshold=threshold,
        )

    def low_rank_approximation(self, rank: int) -> "LinearOperator":
        if rank < 0 or rank > min(self.matrix.shape):
            raise ValueError("rank is outside the admissible range")
        u, singular_values, vh = np.linalg.svd(self.matrix, full_matrices=False)
        approximation = (u[:, :rank] * singular_values[:rank]) @ vh[:rank, :]
        return LinearOperator(
            approximation,
            self.domain,
            self.codomain,
            name=f"{self.name}_rank_{rank}",
            metadata={**self.metadata, "source": self.name, "rank": rank},
        )

    def change_basis(self, domain_basis: npt.ArrayLike, codomain_basis: npt.ArrayLike) -> "LinearOperator":
        """Return coordinates in new bases whose columns are expressed in old coordinates."""
        p = _as_float_array(domain_basis, ndim=2)
        q = _as_float_array(codomain_basis, ndim=2)
        if p.shape != (self.domain.dimension, self.domain.dimension):
            raise ValueError("domain basis must be square and dimension-compatible")
        if q.shape != (self.codomain.dimension, self.codomain.dimension):
            raise ValueError("codomain basis must be square and dimension-compatible")
        transformed = np.linalg.solve(q, self.matrix @ p)
        return LinearOperator(transformed, self.domain, self.codomain, name=f"{self.name}_basis")

    def adjoint_matrix(self) -> Array:
        """Metric adjoint G_domain^{-1} A^T G_codomain."""
        assert self.domain.metric is not None and self.codomain.metric is not None
        return np.linalg.solve(self.domain.metric, self.matrix.T @ self.codomain.metric)
