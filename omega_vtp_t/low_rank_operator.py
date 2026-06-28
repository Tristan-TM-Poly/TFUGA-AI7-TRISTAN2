"""Low-rank operator compression for Ω-VTP-T++.

This module provides reusable SVD compression for lifted linear operators.
It is intentionally NumPy-only and OAK-reported.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LowRankOperator:
    u: np.ndarray
    singular_values: np.ndarray
    vt: np.ndarray
    rank: int
    relative_error: float
    compression_ratio: float
    oak_status: str

    def reconstruct(self) -> np.ndarray:
        return (self.u * self.singular_values) @ self.vt

    def apply(self, x: np.ndarray) -> np.ndarray:
        """Apply the compressed operator to row samples x using y = x @ A.T."""

        arr = np.asarray(x, dtype=float)
        return arr @ self.reconstruct().T


def compress_operator_svd(
    operator: np.ndarray,
    *,
    rank: int | None = None,
    energy_tol: float = 0.999,
) -> LowRankOperator:
    """Compress an operator with truncated SVD.

    Args:
        operator: Matrix A.
        rank: Optional explicit rank. If omitted, choose the smallest rank whose
            captured squared-singular-value energy exceeds energy_tol.
        energy_tol: Energy threshold in (0, 1].
    """

    A = np.asarray(operator, dtype=float)
    if A.ndim != 2:
        raise ValueError("operator must be a 2D matrix")
    if not 0.0 < energy_tol <= 1.0:
        raise ValueError("energy_tol must be in (0, 1]")

    u, s, vt = np.linalg.svd(A, full_matrices=False)
    if s.size == 0:
        chosen_rank = 0
    elif rank is None:
        energy = np.cumsum(s * s) / max(float(np.sum(s * s)), np.finfo(float).eps)
        chosen_rank = int(np.searchsorted(energy, energy_tol) + 1)
    else:
        if rank < 1:
            raise ValueError("rank must be >= 1")
        chosen_rank = min(rank, s.size)

    u_r = u[:, :chosen_rank]
    s_r = s[:chosen_rank]
    vt_r = vt[:chosen_rank, :]
    approx = (u_r * s_r) @ vt_r
    err = np.linalg.norm(A - approx) / max(np.linalg.norm(A), np.finfo(float).eps)
    original_params = A.shape[0] * A.shape[1]
    compressed_params = chosen_rank * (A.shape[0] + A.shape[1] + 1)
    ratio = float(original_params / max(compressed_params, 1))

    if err <= 1e-10:
        status = "certified_lossless_numeric"
    elif err <= 1e-6:
        status = "checked_low_loss"
    elif err <= 1e-2:
        status = "experimental_low_rank"
    else:
        status = "m_minus_loss_high"

    return LowRankOperator(
        u=u_r,
        singular_values=s_r,
        vt=vt_r,
        rank=chosen_rank,
        relative_error=float(err),
        compression_ratio=ratio,
        oak_status=status,
    )
