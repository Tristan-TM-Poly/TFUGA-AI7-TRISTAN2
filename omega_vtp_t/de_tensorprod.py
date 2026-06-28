"""Differential-equation TensorProd tools for Ω-VTP-T++.

This module adds a first OAK-safe Carleman/TensorProd layer for polynomial
ODEs. It constructs the finite lifted operator

    d/dt Phi_J(x) = A_J Phi_J(x) + r_J

where r_J stores terms that leave the truncated feature space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

import numpy as np

from .tensor_prod_lift import Alpha, multi_indices, tensor_prod_lift


@dataclass(frozen=True)
class PolynomialODE:
    """Polynomial ODE dx/dt = f(x).

    coefficients[i][beta] is the coefficient of x**beta in f_i(x).
    """

    dimension: int
    coefficients: Tuple[Mapping[Alpha, float], ...]

    def __post_init__(self) -> None:
        if self.dimension < 1:
            raise ValueError("dimension must be >= 1")
        if len(self.coefficients) != self.dimension:
            raise ValueError("coefficients must contain one mapping per state dimension")
        for component in self.coefficients:
            for alpha in component:
                if len(alpha) != self.dimension:
                    raise ValueError("all multi-indices must match ODE dimension")

    def rhs(self, samples: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
        """Evaluate f(x) for sample matrix shape (n_samples, dimension)."""

        x = np.asarray(samples, dtype=float)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        if x.ndim != 2 or x.shape[1] != self.dimension:
            raise ValueError("samples must have shape (n_samples, dimension)")

        out = np.zeros_like(x, dtype=float)
        for i, component in enumerate(self.coefficients):
            for alpha, coeff in component.items():
                powers = np.asarray(alpha, dtype=int)
                out[:, i] += float(coeff) * np.prod(np.power(x, powers), axis=1)
        return out


@dataclass(frozen=True)
class CarlemanResidualTerm:
    source_alpha: Alpha
    target_alpha: Alpha
    coefficient: float
    reason: str


@dataclass(frozen=True)
class CarlemanTensorProdOperator:
    """Finite Carleman/TensorProd operator for a polynomial ODE."""

    degree: int
    alphas: Tuple[Alpha, ...]
    operator: np.ndarray
    residual_terms: Tuple[CarlemanResidualTerm, ...]
    closure_coefficient: float
    oak_status: str


def build_carleman_operator(ode: PolynomialODE, degree: int) -> CarlemanTensorProdOperator:
    """Build A_J for d/dt Phi_J(x) = A_J Phi_J(x) + r_J.

    For z_alpha = x**alpha:
        d z_alpha / dt = sum_i alpha_i x**(alpha-e_i) f_i(x)
    """

    if degree < 0:
        raise ValueError("degree must be >= 0")

    alphas = multi_indices(ode.dimension, degree)
    index = {alpha: idx for idx, alpha in enumerate(alphas)}
    A = np.zeros((len(alphas), len(alphas)), dtype=float)
    residual_terms = []
    kept_abs = 0.0
    dropped_abs = 0.0

    for row_alpha in alphas:
        row = index[row_alpha]
        for i, alpha_i in enumerate(row_alpha):
            if alpha_i == 0:
                continue
            base = list(row_alpha)
            base[i] -= 1
            for beta, coeff in ode.coefficients[i].items():
                target = tuple(base[j] + beta[j] for j in range(ode.dimension))
                value = float(alpha_i) * float(coeff)
                if target in index:
                    A[row, index[target]] += value
                    kept_abs += abs(value)
                else:
                    residual_terms.append(
                        CarlemanResidualTerm(
                            source_alpha=row_alpha,
                            target_alpha=target,
                            coefficient=value,
                            reason="degree_truncation",
                        )
                    )
                    dropped_abs += abs(value)

    closure = kept_abs / max(kept_abs + dropped_abs, np.finfo(float).eps)
    if not residual_terms:
        status = "closed_in_truncated_space"
    elif closure > 0.99:
        status = "nearly_closed_with_truncation_residual"
    else:
        status = "experimental_truncation_residual_high"

    return CarlemanTensorProdOperator(
        degree=degree,
        alphas=alphas,
        operator=A,
        residual_terms=tuple(residual_terms),
        closure_coefficient=float(closure),
        oak_status=status,
    )


def lifted_time_derivative(
    ode: PolynomialODE,
    samples: Sequence[Sequence[float]] | np.ndarray,
    degree: int,
) -> np.ndarray:
    """Compute d/dt Phi_J(x) directly by chain rule samples."""

    x = np.asarray(samples, dtype=float)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if x.ndim != 2 or x.shape[1] != ode.dimension:
        raise ValueError("samples must have shape (n_samples, dimension)")

    rhs = ode.rhs(x)
    alphas = multi_indices(ode.dimension, degree)
    out = np.zeros((x.shape[0], len(alphas)), dtype=float)

    for col, alpha in enumerate(alphas):
        for i, alpha_i in enumerate(alpha):
            if alpha_i == 0:
                continue
            base = np.array(alpha, dtype=int)
            base[i] -= 1
            out[:, col] += alpha_i * np.prod(np.power(x, base), axis=1) * rhs[:, i]
    return out


def carleman_residual_on_samples(
    ode: PolynomialODE,
    samples: Sequence[Sequence[float]] | np.ndarray,
    degree: int,
) -> dict[str, float | int | str]:
    """Compare direct chain-rule derivative to truncated A_J Phi_J(x)."""

    carleman = build_carleman_operator(ode, degree)
    phi = tensor_prod_lift(samples, degree).features
    direct = lifted_time_derivative(ode, samples, degree)
    predicted = phi @ carleman.operator.T
    err = direct - predicted
    residual_norm = float(np.linalg.norm(err))
    relative = residual_norm / max(float(np.linalg.norm(direct)), np.finfo(float).eps)
    return {
        "degree": degree,
        "feature_count": len(carleman.alphas),
        "residual_term_count": len(carleman.residual_terms),
        "closure_coefficient": carleman.closure_coefficient,
        "sample_relative_residual": float(relative),
        "sample_residual_norm": residual_norm,
        "oak_status": carleman.oak_status,
    }
