"""Finite commutant and simultaneous-centralizer solvers.

For a square matrix A, vec(AX-XA) = (I⊗A - Aᵀ⊗I)vec(X) in column-major
ordering. Null spaces are estimated by SVD and accompanied by residual audits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.complex128]


class CommutantError(ValueError):
    pass


@dataclass(frozen=True)
class CommutantReport:
    matrix_count: int
    dimension: int
    ambient_dimension: int
    nullity: int
    tolerance: float
    singular_values: tuple[float, ...]
    basis: tuple[Array, ...]
    maximum_commutator_residual: float
    identity_in_span_residual: float
    finite: bool
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["basis_real"] = [value.real.tolist() for value in self.basis]
        payload["basis_imag"] = [value.imag.tolist() for value in self.basis]
        payload.pop("basis")
        return payload


def _square_matrix(value: npt.ArrayLike) -> Array:
    matrix = np.asarray(value, dtype=np.complex128)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise CommutantError("commutant solvers require square matrices")
    if not np.all(np.isfinite(matrix)):
        raise CommutantError("commutant matrices must be finite")
    return matrix


def _constraint(matrix: Array) -> Array:
    n = matrix.shape[0]
    identity = np.eye(n, dtype=np.complex128)
    return np.kron(identity, matrix) - np.kron(matrix.T, identity)


def _relative_commutator(matrix: Array, candidate: Array) -> float:
    numerator = matrix @ candidate - candidate @ matrix
    scale = max(
        float(np.linalg.norm(matrix, ord="fro") * np.linalg.norm(candidate, ord="fro")),
        np.finfo(float).eps,
    )
    return float(np.linalg.norm(numerator, ord="fro") / scale)


def simultaneous_commutant_basis(
    matrices: Iterable[npt.ArrayLike],
    *,
    relative_tolerance: float | None = None,
    max_dimension: int = 64,
) -> CommutantReport:
    arrays = tuple(_square_matrix(value) for value in matrices)
    if not arrays:
        raise CommutantError("at least one matrix is required")
    dimension = arrays[0].shape[0]
    if dimension > max_dimension:
        raise CommutantError("commutant dense SVD exceeds max_dimension")
    if any(value.shape != arrays[0].shape for value in arrays[1:]):
        raise CommutantError("simultaneous commutant matrices must share shape")

    stacked = np.vstack([_constraint(value) for value in arrays])
    _, singular_values, vh = np.linalg.svd(stacked, full_matrices=True)
    largest = float(singular_values[0]) if singular_values.size else 0.0
    tolerance = relative_tolerance
    if tolerance is None:
        tolerance = max(stacked.shape) * np.finfo(float).eps * max(largest, 1.0)
    if tolerance < 0:
        raise CommutantError("tolerance cannot be negative")
    rank = int(np.sum(singular_values > tolerance))
    nullity = dimension * dimension - rank
    null_vectors = vh.conj().T[:, rank:]
    basis: list[Array] = []
    for index in range(null_vectors.shape[1]):
        candidate = null_vectors[:, index].reshape(
            (dimension, dimension), order="F"
        )
        norm = float(np.linalg.norm(candidate, ord="fro"))
        if norm > 0:
            candidate = candidate / norm
        basis.append(candidate)

    maximum = 0.0
    for candidate in basis:
        for matrix in arrays:
            maximum = max(maximum, _relative_commutator(matrix, candidate))

    identity = np.eye(dimension, dtype=np.complex128)
    if basis:
        basis_matrix = np.column_stack(
            [candidate.reshape(-1, order="F") for candidate in basis]
        )
        coefficients, *_ = np.linalg.lstsq(
            basis_matrix,
            identity.reshape(-1, order="F"),
            rcond=None,
        )
        reconstructed = (basis_matrix @ coefficients).reshape(
            (dimension, dimension), order="F"
        )
        identity_residual = float(
            np.linalg.norm(reconstructed - identity, ord="fro")
            / max(np.linalg.norm(identity, ord="fro"), np.finfo(float).eps)
        )
    else:
        identity_residual = 1.0

    finite = all(np.all(np.isfinite(candidate)) for candidate in basis)
    return CommutantReport(
        matrix_count=len(arrays),
        dimension=dimension,
        ambient_dimension=dimension * dimension,
        nullity=nullity,
        tolerance=float(tolerance),
        singular_values=tuple(float(value) for value in singular_values),
        basis=tuple(basis),
        maximum_commutator_residual=maximum,
        identity_in_span_residual=identity_residual,
        finite=finite,
    )


def commutant_basis(
    matrix: npt.ArrayLike,
    *,
    relative_tolerance: float | None = None,
    max_dimension: int = 64,
) -> CommutantReport:
    return simultaneous_commutant_basis(
        (matrix,),
        relative_tolerance=relative_tolerance,
        max_dimension=max_dimension,
    )


def commutes_with_basis(
    matrix: npt.ArrayLike,
    basis: Iterable[npt.ArrayLike],
    *,
    tolerance: float = 1e-10,
) -> tuple[bool, float]:
    a = _square_matrix(matrix)
    maximum = 0.0
    for candidate in basis:
        x = _square_matrix(candidate)
        if x.shape != a.shape:
            raise CommutantError("basis matrix shape mismatch")
        maximum = max(maximum, _relative_commutator(a, x))
    return maximum <= tolerance, maximum
