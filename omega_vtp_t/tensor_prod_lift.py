"""TensorProd-Lift de Tristan.

This module implements the computational kernel behind

    Phi_J(v) = Tensor_prod_{i,j} (1 + v_i)^{○j}

in two practical bases:

1. Monomial basis:
       Phi_J(v) = [v^alpha for alpha in N^n, |alpha| <= J]
   This is the cleanest basis for exact polynomial linearization.

2. One-plus basis:
       Psi_J(v) = [prod_i (1 + v_i)^{j_i}]
   This follows the proposed notation directly. It is binomially mixed and can
   span the same polynomial space when used carefully.

OAK-safe statement:
    A polynomial F(v) of total degree <= J can be represented exactly as a
    linear functional of Phi_J(v). Non-polynomial, analytic, discontinuous, or
    chaotic systems require truncation/approximation and a measured residual.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from time import perf_counter
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

Alpha = Tuple[int, ...]


@dataclass(frozen=True)
class LiftResult:
    """Result of a feature lift.

    Attributes:
        features: Array of shape (n_samples, n_features).
        alphas: Multi-index labels for each feature.
        basis: Either "monomial" or "one_plus".
        degree: Maximum degree used by the lift.
    """

    features: np.ndarray
    alphas: Tuple[Alpha, ...]
    basis: str
    degree: int


@dataclass(frozen=True)
class OAKReport:
    """Minimal OAK report for a lifted linearization."""

    residual_norm: float
    relative_residual: float
    max_abs_error: float
    condition_number: float
    feature_count: int
    sample_count: int
    rank: int
    oak_status: str


@dataclass(frozen=True)
class LinearOperatorFit:
    """Least-squares fit of Y ≈ X @ W.T in lifted coordinates."""

    operator: np.ndarray
    report: OAKReport


def _as_2d_samples(v: np.ndarray | Sequence[float]) -> np.ndarray:
    x = np.asarray(v, dtype=float)
    if x.ndim == 0:
        raise ValueError("v must contain at least one variable.")
    if x.ndim == 1:
        return x.reshape(1, -1)
    if x.ndim == 2:
        return x
    raise ValueError("v must be a 1D vector or a 2D sample matrix.")


def feature_count(n_variables: int, degree: int) -> int:
    """Number of monomials with total degree <= degree in n_variables.

    Formula:
        C(n_variables + degree, degree)
    """

    if n_variables < 1:
        raise ValueError("n_variables must be >= 1.")
    if degree < 0:
        raise ValueError("degree must be >= 0.")
    return comb(n_variables + degree, degree)


def _weak_compositions(total: int, parts: int) -> Iterable[Alpha]:
    """Yield alpha in N^parts with sum(alpha) == total."""

    if parts == 1:
        yield (total,)
        return

    for first in range(total + 1):
        for rest in _weak_compositions(total - first, parts - 1):
            yield (first,) + rest


def multi_indices(n_variables: int, degree: int, *, exact_degree: bool = False) -> Tuple[Alpha, ...]:
    """Return all multi-indices alpha in N^n.

    Args:
        n_variables: Number of variables.
        degree: Maximum total degree, or exact degree when exact_degree=True.
        exact_degree: If true, return only |alpha| == degree.

    Returns:
        Tuple of multi-indices ordered by increasing total degree, then
        lexicographic weak composition order.
    """

    if n_variables < 1:
        raise ValueError("n_variables must be >= 1.")
    if degree < 0:
        raise ValueError("degree must be >= 0.")

    totals = [degree] if exact_degree else range(degree + 1)
    out: List[Alpha] = []
    for total in totals:
        out.extend(_weak_compositions(total, n_variables))
    return tuple(out)


def tensor_prod_lift(v: np.ndarray | Sequence[float], degree: int) -> LiftResult:
    """Compute the monomial TensorProd lift Phi_J(v).

    For v with shape (n_variables,), returns features of shape (1, n_features).
    For v with shape (n_samples, n_variables), returns shape
    (n_samples, n_features).

    The returned feature columns are v**alpha for all |alpha| <= degree.
    """

    x = _as_2d_samples(v)
    n_variables = x.shape[1]
    alphas = multi_indices(n_variables, degree)

    columns = []
    for alpha in alphas:
        a = np.asarray(alpha, dtype=int)
        columns.append(np.prod(np.power(x, a), axis=1))
    features = np.column_stack(columns) if columns else np.empty((x.shape[0], 0))

    return LiftResult(features=features, alphas=alphas, basis="monomial", degree=degree)


def one_plus_lift(v: np.ndarray | Sequence[float], degree: int, *, total_degree: bool = False) -> LiftResult:
    """Compute the one-plus lift Psi_J(v) = prod_i (1 + v_i)^j_i.

    Args:
        v: 1D vector or 2D sample matrix.
        degree: Degree bound.
        total_degree: If true, keep exponents j with |j| <= degree. If false,
            use every j_i in [0, degree], which can create (degree+1)^n features.

    Returns:
        LiftResult in the "one_plus" basis.
    """

    x = _as_2d_samples(v)
    n_variables = x.shape[1]

    if total_degree:
        alphas = multi_indices(n_variables, degree)
    else:
        import itertools

        alphas = tuple(itertools.product(range(degree + 1), repeat=n_variables))

    columns = []
    shifted = 1.0 + x
    for alpha in alphas:
        a = np.asarray(alpha, dtype=int)
        columns.append(np.prod(np.power(shifted, a), axis=1))
    features = np.column_stack(columns) if columns else np.empty((x.shape[0], 0))

    return LiftResult(features=features, alphas=alphas, basis="one_plus", degree=degree)


def polynomial_eval_from_lift(
    v: np.ndarray | Sequence[float],
    degree: int,
    coeffs: Mapping[Alpha, float],
) -> np.ndarray:
    """Evaluate a polynomial using the monomial lift.

    coeffs maps alpha -> coefficient.

    Example:
        F(x, y) = 3 x^2 + 5 xy - 7 y^3 + 2

        coeffs = {
            (0, 0): 2.0,
            (2, 0): 3.0,
            (1, 1): 5.0,
            (0, 3): -7.0,
        }
    """

    lift = tensor_prod_lift(v, degree)
    c = np.array([float(coeffs.get(alpha, 0.0)) for alpha in lift.alphas])
    return lift.features @ c


def fit_linear_operator(
    x_lifted: np.ndarray,
    y_lifted: np.ndarray,
    *,
    rcond: float | None = None,
    certify_tol: float = 1e-10,
) -> LinearOperatorFit:
    """Fit a linear operator A such that y_lifted ≈ x_lifted @ A.T.

    Args:
        x_lifted: Matrix of shape (n_samples, n_features_in).
        y_lifted: Matrix of shape (n_samples, n_features_out).
        rcond: Least-squares cutoff passed to numpy.linalg.lstsq.
        certify_tol: Relative residual threshold for status "certified".

    Returns:
        LinearOperatorFit with operator A of shape
        (n_features_out, n_features_in).
    """

    x = np.asarray(x_lifted, dtype=float)
    y = np.asarray(y_lifted, dtype=float)
    if x.ndim != 2 or y.ndim != 2:
        raise ValueError("x_lifted and y_lifted must be 2D matrices.")
    if x.shape[0] != y.shape[0]:
        raise ValueError("x_lifted and y_lifted must have the same sample count.")

    solution, residuals, rank, singular_values = np.linalg.lstsq(x, y, rcond=rcond)
    operator = solution.T
    prediction = x @ solution
    error = y - prediction

    residual_norm = float(np.linalg.norm(error))
    y_norm = float(np.linalg.norm(y))
    relative_residual = residual_norm / max(y_norm, np.finfo(float).eps)
    max_abs_error = float(np.max(np.abs(error))) if error.size else 0.0
    if singular_values.size == 0 or np.min(singular_values) == 0:
        condition_number = float("inf")
    else:
        condition_number = float(np.max(singular_values) / np.min(singular_values))

    if relative_residual <= certify_tol:
        status = "certified"
    elif relative_residual <= 1e-6:
        status = "checked"
    else:
        status = "experimental_residual_high"

    report = OAKReport(
        residual_norm=residual_norm,
        relative_residual=relative_residual,
        max_abs_error=max_abs_error,
        condition_number=condition_number,
        feature_count=x.shape[1],
        sample_count=x.shape[0],
        rank=int(rank),
        oak_status=status,
    )
    return LinearOperatorFit(operator=operator, report=report)


def benchmark_lift(
    samples: np.ndarray | Sequence[Sequence[float]],
    degree: int,
    *,
    basis: str = "monomial",
    repeats: int = 5,
) -> Dict[str, float | int | str]:
    """Small timing benchmark for OAK-style reports."""

    x = _as_2d_samples(samples)
    if repeats < 1:
        raise ValueError("repeats must be >= 1.")

    fn = tensor_prod_lift if basis == "monomial" else one_plus_lift

    times = []
    last = None
    for _ in range(repeats):
        start = perf_counter()
        last = fn(x, degree)
        times.append(perf_counter() - start)

    assert last is not None
    return {
        "basis": basis,
        "degree": degree,
        "sample_count": x.shape[0],
        "input_dimension": x.shape[1],
        "feature_count": last.features.shape[1],
        "best_seconds": min(times),
        "mean_seconds": float(np.mean(times)),
        "memory_bytes": int(last.features.nbytes),
    }
