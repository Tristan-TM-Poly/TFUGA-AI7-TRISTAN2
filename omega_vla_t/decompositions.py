"""Structured linear-algebra decompositions for Ω-VLA-T∞."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.float64]


def _matrix(value: npt.ArrayLike, *, square: bool = False) -> Array:
    matrix = np.asarray(value, dtype=float)
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise ValueError("expected a finite matrix")
    if square and matrix.shape[0] != matrix.shape[1]:
        raise ValueError("expected a square matrix")
    return matrix


@dataclass(frozen=True)
class SymmetryDecomposition:
    symmetric: Array
    skew_symmetric: Array
    reconstruction_error: float
    orthogonality_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "symmetric": self.symmetric.tolist(),
            "skew_symmetric": self.skew_symmetric.tolist(),
            "reconstruction_error": self.reconstruction_error,
            "orthogonality_error": self.orthogonality_error,
        }


def decompose_symmetric_skew(matrix: npt.ArrayLike) -> SymmetryDecomposition:
    value = _matrix(matrix, square=True)
    symmetric = 0.5 * (value + value.T)
    skew = 0.5 * (value - value.T)
    reconstruction = float(np.linalg.norm(value - symmetric - skew))
    orthogonality = float(abs(np.vdot(symmetric, skew)))
    return SymmetryDecomposition(symmetric, skew, reconstruction, orthogonality)


def commutator(left: npt.ArrayLike, right: npt.ArrayLike) -> Array:
    a = _matrix(left, square=True)
    b = _matrix(right, square=True)
    if a.shape != b.shape:
        raise ValueError("commutator matrices must have identical shapes")
    return a @ b - b @ a


def anticommutator(left: npt.ArrayLike, right: npt.ArrayLike) -> Array:
    a = _matrix(left, square=True)
    b = _matrix(right, square=True)
    if a.shape != b.shape:
        raise ValueError("anticommutator matrices must have identical shapes")
    return a @ b + b @ a


def orthonormal_basis(vectors: npt.ArrayLike, *, tolerance: float = 1e-12) -> Array:
    """Return a column-orthonormal basis for the numerical column space."""
    matrix = _matrix(vectors)
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    u, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
    if singular_values.size == 0:
        return np.zeros((matrix.shape[0], 0), dtype=float)
    threshold = tolerance * max(matrix.shape) * max(float(singular_values[0]), 1.0)
    rank = int(np.count_nonzero(singular_values > threshold))
    return u[:, :rank]


def orthogonal_projector(vectors: npt.ArrayLike, *, tolerance: float = 1e-12) -> Array:
    basis = orthonormal_basis(vectors, tolerance=tolerance)
    return basis @ basis.T


def metric_projector(vectors: npt.ArrayLike, metric: npt.ArrayLike) -> Array:
    """Project onto col(V) under inner product xᵀG y."""
    v = _matrix(vectors)
    g = _matrix(metric, square=True)
    if g.shape != (v.shape[0], v.shape[0]):
        raise ValueError("metric dimension must match vector ambient dimension")
    if not np.allclose(g, g.T, atol=1e-12, rtol=0.0):
        raise ValueError("metric must be symmetric")
    if np.min(np.linalg.eigvalsh(g)) <= 0:
        raise ValueError("metric must be positive definite")
    gram = v.T @ g @ v
    return v @ np.linalg.pinv(gram) @ v.T @ g


def projection_residual(projector: npt.ArrayLike, vector: npt.ArrayLike) -> tuple[Array, Array]:
    p = _matrix(projector, square=True)
    x = np.asarray(vector, dtype=float)
    if x.shape != (p.shape[0],):
        raise ValueError("vector dimension must match projector")
    projected = p @ x
    return projected, x - projected


def principal_angles(left_basis: npt.ArrayLike, right_basis: npt.ArrayLike) -> Array:
    """Principal angles between two numerical column spaces in radians."""
    q_left = orthonormal_basis(left_basis)
    q_right = orthonormal_basis(right_basis)
    if q_left.shape[0] != q_right.shape[0]:
        raise ValueError("subspaces must share an ambient dimension")
    if q_left.shape[1] == 0 or q_right.shape[1] == 0:
        return np.array([], dtype=float)
    singular_values = np.linalg.svd(q_left.T @ q_right, compute_uv=False)
    return np.arccos(np.clip(singular_values, -1.0, 1.0))


@dataclass(frozen=True)
class ProjectorAudit:
    idempotence_error: float
    symmetry_error: float
    rank: int
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "idempotence_error": self.idempotence_error,
            "symmetry_error": self.symmetry_error,
            "rank": self.rank,
            "passed": self.passed,
        }


def audit_orthogonal_projector(projector: npt.ArrayLike, *, tolerance: float = 1e-10) -> ProjectorAudit:
    p = _matrix(projector, square=True)
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    idempotence = float(np.linalg.norm(p @ p - p))
    symmetry = float(np.linalg.norm(p.T - p))
    return ProjectorAudit(
        idempotence_error=idempotence,
        symmetry_error=symmetry,
        rank=int(np.linalg.matrix_rank(p)),
        passed=idempotence <= tolerance and symmetry <= tolerance,
    )
