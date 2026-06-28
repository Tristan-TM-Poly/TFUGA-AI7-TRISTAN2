"""Orthogonal and stabilized lift bases for Ω-VTP-T++ v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

from .tensor_prod_lift import Alpha, LiftResult, multi_indices


@dataclass(frozen=True)
class ScalingDomain:
    """Affine scaling domain for mapping samples into [-1, 1]."""

    lower: Tuple[float, ...]
    upper: Tuple[float, ...]

    def as_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        return np.asarray(self.lower, dtype=float), np.asarray(self.upper, dtype=float)


def infer_scaling_domain(samples: Sequence[Sequence[float]] | np.ndarray, *, margin: float = 0.0) -> ScalingDomain:
    """Infer per-variable min/max domain for stable orthogonal bases."""

    x = np.asarray(samples, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if x.ndim != 2:
        raise ValueError("samples must be a 1D or 2D array.")
    lo = np.min(x, axis=0)
    hi = np.max(x, axis=0)
    span = hi - lo
    lo = lo - margin * span
    hi = hi + margin * span
    return ScalingDomain(tuple(float(v) for v in lo), tuple(float(v) for v in hi))


def scale_to_unit_interval(
    samples: Sequence[Sequence[float]] | np.ndarray,
    domain: ScalingDomain | tuple[Sequence[float], Sequence[float]] | None = None,
) -> tuple[np.ndarray, ScalingDomain]:
    """Scale samples to [-1, 1] per coordinate."""

    x = np.asarray(samples, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if x.ndim != 2:
        raise ValueError("samples must be a 1D or 2D array.")

    if domain is None:
        domain_obj = infer_scaling_domain(x)
    elif isinstance(domain, ScalingDomain):
        domain_obj = domain
    else:
        domain_obj = ScalingDomain(tuple(float(v) for v in domain[0]), tuple(float(v) for v in domain[1]))

    lo, hi = domain_obj.as_arrays()
    if lo.shape[0] != x.shape[1] or hi.shape[0] != x.shape[1]:
        raise ValueError("domain dimension must match sample dimension.")

    span = hi - lo
    safe_span = np.where(np.abs(span) < np.finfo(float).eps, 1.0, span)
    scaled = 2.0 * (x - lo) / safe_span - 1.0
    scaled = np.where(np.abs(span) < np.finfo(float).eps, 0.0, scaled)
    return scaled, domain_obj


def chebyshev_values(x_scaled: np.ndarray, degree: int) -> np.ndarray:
    """Return Chebyshev T_0..T_degree values for every variable."""

    if degree < 0:
        raise ValueError("degree must be >= 0.")
    x = np.asarray(x_scaled, dtype=float)
    if x.ndim != 2:
        raise ValueError("x_scaled must be a 2D matrix.")

    values = np.empty((x.shape[0], x.shape[1], degree + 1), dtype=float)
    values[:, :, 0] = 1.0
    if degree >= 1:
        values[:, :, 1] = x
    for k in range(2, degree + 1):
        values[:, :, k] = 2.0 * x * values[:, :, k - 1] - values[:, :, k - 2]
    return values


def chebyshev_lift(
    samples: Sequence[Sequence[float]] | np.ndarray,
    degree: int,
    *,
    domain: ScalingDomain | tuple[Sequence[float], Sequence[float]] | None = None,
) -> LiftResult:
    """Tensor-product Chebyshev lift with total degree <= degree.

    This is a numerically safer alternative to raw monomials on bounded domains.
    Feature alpha is prod_i T_{alpha_i}(scaled_x_i).
    """

    scaled, _ = scale_to_unit_interval(samples, domain=domain)
    n_variables = scaled.shape[1]
    alphas = multi_indices(n_variables, degree)
    values = chebyshev_values(scaled, degree)

    columns = []
    for alpha in alphas:
        col = np.ones(scaled.shape[0], dtype=float)
        for variable_idx, basis_degree in enumerate(alpha):
            col *= values[:, variable_idx, basis_degree]
        columns.append(col)

    features = np.column_stack(columns) if columns else np.empty((scaled.shape[0], 0))
    return LiftResult(features=features, alphas=alphas, basis="chebyshev", degree=degree)
