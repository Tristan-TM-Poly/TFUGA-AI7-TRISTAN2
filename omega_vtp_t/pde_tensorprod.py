"""PDE helpers for Ω-VTP-T++ differential-equation TensorProd.

The most practical first path is method-of-lines:

    PDE -> spatial discretization -> large ODE -> TensorProd/Koopman/Carleman

This module provides small, dependency-light finite-difference utilities and
OAK residual/conservation checks for 1D periodic PDE prototypes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class PDEResidualReport:
    residual_norm: float
    relative_residual: float
    max_abs_residual: float
    boundary_residual: float
    conservation_residual: float
    oak_status: str


def laplacian_1d_periodic(u: Sequence[float] | np.ndarray, dx: float) -> np.ndarray:
    """Second-order periodic finite-difference Laplacian."""

    if dx <= 0:
        raise ValueError("dx must be > 0")
    arr = np.asarray(u, dtype=float)
    if arr.ndim != 1:
        raise ValueError("u must be a 1D field")
    return (np.roll(arr, -1) - 2.0 * arr + np.roll(arr, 1)) / (dx * dx)


def gradient_1d_periodic(u: Sequence[float] | np.ndarray, dx: float) -> np.ndarray:
    """Second-order central periodic gradient."""

    if dx <= 0:
        raise ValueError("dx must be > 0")
    arr = np.asarray(u, dtype=float)
    if arr.ndim != 1:
        raise ValueError("u must be a 1D field")
    return (np.roll(arr, -1) - np.roll(arr, 1)) / (2.0 * dx)


def reaction_diffusion_rhs(
    u: Sequence[float] | np.ndarray,
    *,
    dx: float,
    diffusion: float,
    reaction: Callable[[np.ndarray], np.ndarray] | None = None,
) -> np.ndarray:
    """Periodic 1D reaction-diffusion RHS: du/dt = D u_xx + R(u)."""

    arr = np.asarray(u, dtype=float)
    if diffusion < 0:
        raise ValueError("diffusion must be >= 0")
    r = np.zeros_like(arr) if reaction is None else np.asarray(reaction(arr), dtype=float)
    if r.shape != arr.shape:
        raise ValueError("reaction(u) must return the same shape as u")
    return diffusion * laplacian_1d_periodic(arr, dx) + r


def burgers_rhs_periodic(
    u: Sequence[float] | np.ndarray,
    *,
    dx: float,
    viscosity: float,
) -> np.ndarray:
    """Periodic viscous Burgers RHS: du/dt = -u u_x + nu u_xx."""

    arr = np.asarray(u, dtype=float)
    if viscosity < 0:
        raise ValueError("viscosity must be >= 0")
    return -arr * gradient_1d_periodic(arr, dx) + viscosity * laplacian_1d_periodic(arr, dx)


def periodic_boundary_residual(u: Sequence[float] | np.ndarray) -> float:
    """Boundary mismatch for periodic fields using endpoint difference."""

    arr = np.asarray(u, dtype=float)
    if arr.ndim != 1:
        raise ValueError("u must be a 1D field")
    if arr.size < 2:
        return 0.0
    return float(abs(arr[0] - arr[-1]))


def mass(u: Sequence[float] | np.ndarray, dx: float) -> float:
    """Discrete integral of a 1D field."""

    if dx <= 0:
        raise ValueError("dx must be > 0")
    return float(np.sum(np.asarray(u, dtype=float)) * dx)


def pde_residual_euler(
    u_now: Sequence[float] | np.ndarray,
    u_next: Sequence[float] | np.ndarray,
    *,
    dt: float,
    rhs_now: Sequence[float] | np.ndarray,
    dx: float,
    conserved_mass_initial: float | None = None,
) -> PDEResidualReport:
    """OAK residual for one explicit-Euler PDE step.

    residual = (u_next - u_now)/dt - rhs_now
    """

    if dt <= 0:
        raise ValueError("dt must be > 0")
    now = np.asarray(u_now, dtype=float)
    nxt = np.asarray(u_next, dtype=float)
    rhs = np.asarray(rhs_now, dtype=float)
    if now.shape != nxt.shape or now.shape != rhs.shape:
        raise ValueError("u_now, u_next, and rhs_now must have the same shape")

    residual = (nxt - now) / dt - rhs
    norm = float(np.linalg.norm(residual))
    denom = max(float(np.linalg.norm(rhs)), np.finfo(float).eps)
    rel = norm / denom
    max_abs = float(np.max(np.abs(residual))) if residual.size else 0.0
    boundary = periodic_boundary_residual(nxt)
    if conserved_mass_initial is None:
        conservation = 0.0
    else:
        conservation = abs(mass(nxt, dx) - float(conserved_mass_initial))

    if rel <= 1e-10 and conservation <= 1e-10:
        status = "certified_step"
    elif rel <= 1e-6:
        status = "checked_step"
    elif rel <= 1e-2:
        status = "experimental_step"
    else:
        status = "residual_high"

    return PDEResidualReport(
        residual_norm=norm,
        relative_residual=float(rel),
        max_abs_residual=max_abs,
        boundary_residual=boundary,
        conservation_residual=float(conservation),
        oak_status=status,
    )
