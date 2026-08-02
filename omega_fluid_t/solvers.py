from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi, sin
from typing import Callable


@dataclass(frozen=True)
class DiffusionResult:
    x: tuple[float, ...]
    values: tuple[float, ...]
    time: float
    dx: float
    dt: float
    steps: int
    cfl_diffusion: float
    initial_mass: float
    final_mass: float

    @property
    def boundary_mass_loss(self) -> float:
        return self.initial_mass - self.final_mass


def _trapezoid(values: list[float], dx: float) -> float:
    if len(values) < 2:
        return 0.0
    return dx * (0.5 * values[0] + sum(values[1:-1]) + 0.5 * values[-1])


def solve_diffusion_1d(
    *,
    points: int,
    final_time: float,
    diffusivity: float,
    initial: Callable[[float], float] | None = None,
    stability_factor: float = 0.45,
) -> DiffusionResult:
    """Explicit centered solver for u_t = diffusivity * u_xx on [0, 1].

    Homogeneous Dirichlet boundaries are enforced. The time step is selected
    from the diffusion CFL and adjusted to land exactly at final_time.
    """
    if points < 3:
        raise ValueError("points must be at least 3")
    if final_time < 0 or diffusivity <= 0:
        raise ValueError("final_time must be non-negative and diffusivity positive")
    if not 0 < stability_factor <= 0.5:
        raise ValueError("stability_factor must lie in (0, 0.5]")

    initial = initial or (lambda x: sin(pi * x))
    dx = 1.0 / (points - 1)
    x = [i * dx for i in range(points)]
    u = [float(initial(position)) for position in x]
    u[0] = 0.0
    u[-1] = 0.0
    initial_mass = _trapezoid(u, dx)

    if final_time == 0:
        return DiffusionResult(tuple(x), tuple(u), 0.0, dx, 0.0, 0, 0.0, initial_mass, initial_mass)

    maximum_dt = stability_factor * dx * dx / diffusivity
    steps = max(1, ceil(final_time / maximum_dt))
    dt = final_time / steps
    ratio = diffusivity * dt / (dx * dx)

    for _ in range(steps):
        next_u = u.copy()
        for i in range(1, points - 1):
            next_u[i] = u[i] + ratio * (u[i + 1] - 2.0 * u[i] + u[i - 1])
        next_u[0] = 0.0
        next_u[-1] = 0.0
        u = next_u

    return DiffusionResult(
        x=tuple(x),
        values=tuple(u),
        time=final_time,
        dx=dx,
        dt=dt,
        steps=steps,
        cfl_diffusion=ratio,
        initial_mass=initial_mass,
        final_mass=_trapezoid(u, dx),
    )
