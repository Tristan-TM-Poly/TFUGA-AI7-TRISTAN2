"""Small lifted linear solvers for Ω-VTP-T++.

The purpose is reusable OAK experiments, not a replacement for SciPy solvers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class LinearSolveReport:
    method: str
    steps: int
    dt: float
    residual_norm: float
    oak_status: str


def rk4_linear_step(z: np.ndarray, A: np.ndarray, dt: float) -> np.ndarray:
    """One RK4 step for dz/dt = A z, using row-vector states."""

    if dt <= 0:
        raise ValueError("dt must be > 0")
    state = np.asarray(z, dtype=float)
    op = np.asarray(A, dtype=float)
    if op.ndim != 2 or op.shape[0] != op.shape[1]:
        raise ValueError("A must be a square matrix")
    if state.shape[-1] != op.shape[0]:
        raise ValueError("last dimension of z must match A")

    def f(y: np.ndarray) -> np.ndarray:
        return y @ op.T

    k1 = f(state)
    k2 = f(state + 0.5 * dt * k1)
    k3 = f(state + 0.5 * dt * k2)
    k4 = f(state + dt * k3)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def solve_lifted_linear(
    z0: np.ndarray,
    A: np.ndarray,
    *,
    dt: float,
    steps: int,
    method: Literal["euler", "rk4"] = "rk4",
) -> tuple[np.ndarray, LinearSolveReport]:
    """Integrate dz/dt = A z for a small lifted linear system."""

    if steps < 0:
        raise ValueError("steps must be >= 0")
    if dt <= 0:
        raise ValueError("dt must be > 0")

    z = np.asarray(z0, dtype=float)
    op = np.asarray(A, dtype=float)
    trajectory = [z.copy()]

    for _ in range(steps):
        if method == "euler":
            z = z + dt * (z @ op.T)
        elif method == "rk4":
            z = rk4_linear_step(z, op, dt)
        else:
            raise ValueError("method must be 'euler' or 'rk4'")
        trajectory.append(z.copy())

    traj = np.stack(trajectory, axis=0)
    if steps == 0:
        residual = 0.0
    else:
        discrete_derivative = (traj[-1] - traj[-2]) / dt
        predicted = traj[-2] @ op.T
        residual = float(np.linalg.norm(discrete_derivative - predicted))

    status = "checked" if residual <= 1e-6 else "experimental_time_residual"
    return traj, LinearSolveReport(method=method, steps=steps, dt=dt, residual_norm=residual, oak_status=status)
