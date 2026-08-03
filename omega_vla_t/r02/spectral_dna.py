"""Spectral DNA fixtures for finite-dimensional real/complex operators."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import numpy.typing as npt


Array = npt.NDArray[np.complex128]


@dataclass(frozen=True)
class SpectralDNA:
    shape: tuple[int, int]
    eigenvalues_real: tuple[float, ...]
    eigenvalues_imag: tuple[float, ...]
    spectral_radius: float
    spectral_abscissa: float
    singular_values: tuple[float, ...]
    numerical_rank: int
    effective_rank: float
    condition_number: float
    normality_residual: float
    hermitian_residual: float
    unitary_residual: float
    pseudospectral_probe: tuple[tuple[float, float, float], ...]
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _effective_rank(singular_values: np.ndarray) -> float:
    total = float(np.sum(singular_values))
    if total <= 0.0:
        return 0.0
    probabilities = singular_values / total
    probabilities = probabilities[probabilities > 0.0]
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return float(np.exp(entropy))


def _relative_residual(numerator: np.ndarray, reference: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(reference)), np.finfo(float).eps)
    return float(np.linalg.norm(numerator) / denominator)


def _pseudospectral_probe(
    matrix: np.ndarray,
    eigenvalues: np.ndarray,
    points: int,
) -> tuple[tuple[float, float, float], ...]:
    if points <= 0:
        return ()
    radius = max(float(np.max(np.abs(eigenvalues), initial=0.0)), 1.0)
    center = complex(np.mean(eigenvalues)) if eigenvalues.size else 0.0j
    probes: list[tuple[float, float, float]] = []
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    for index in range(points):
        angle = 2.0 * np.pi * index / points
        z = center + 1.25 * radius * np.exp(1j * angle)
        singular = np.linalg.svd(z * identity - matrix, compute_uv=False)
        sigma_min = float(singular[-1]) if singular.size else 0.0
        resolvent_norm = float("inf") if sigma_min == 0.0 else 1.0 / sigma_min
        probes.append((float(z.real), float(z.imag), resolvent_norm))
    return tuple(probes)


def spectral_dna(
    matrix: npt.ArrayLike,
    *,
    rank_tolerance: float | None = None,
    pseudospectral_points: int = 8,
) -> SpectralDNA:
    """Build a bounded numerical signature; this is not a spectral proof."""

    array = np.asarray(matrix, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("spectral_dna requires a square matrix")
    if not np.all(np.isfinite(array)):
        raise ValueError("matrix entries must be finite")

    n = array.shape[0]
    eigenvalues = np.linalg.eigvals(array)
    singular_values = np.linalg.svd(array, compute_uv=False)
    tolerance = rank_tolerance
    if tolerance is None:
        tolerance = (
            max(array.shape)
            * np.finfo(float).eps
            * (float(singular_values[0]) if singular_values.size else 0.0)
        )
    numerical_rank = int(np.sum(singular_values > tolerance))
    condition = float(np.linalg.cond(array)) if n else 0.0

    adjoint = array.conj().T
    normality = _relative_residual(array @ adjoint - adjoint @ array, array)
    hermitian = _relative_residual(array - adjoint, array)
    unitary = _relative_residual(adjoint @ array - np.eye(n), np.eye(n))

    order = np.lexsort((eigenvalues.imag, eigenvalues.real))
    ordered = eigenvalues[order]
    probes = _pseudospectral_probe(array, ordered, pseudospectral_points)

    return SpectralDNA(
        shape=(n, n),
        eigenvalues_real=tuple(float(value.real) for value in ordered),
        eigenvalues_imag=tuple(float(value.imag) for value in ordered),
        spectral_radius=float(np.max(np.abs(ordered), initial=0.0)),
        spectral_abscissa=float(np.max(ordered.real, initial=0.0)),
        singular_values=tuple(float(value) for value in singular_values),
        numerical_rank=numerical_rank,
        effective_rank=_effective_rank(singular_values),
        condition_number=condition,
        normality_residual=normality,
        hermitian_residual=hermitian,
        unitary_residual=unitary,
        pseudospectral_probe=probes,
    )
