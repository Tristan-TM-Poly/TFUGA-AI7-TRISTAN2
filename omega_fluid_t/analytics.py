from __future__ import annotations

from math import pi, sin
from typing import Iterable


def couette_profile(y: float, *, gap: float, lower_velocity: float = 0.0, upper_velocity: float = 1.0) -> float:
    if gap <= 0:
        raise ValueError("gap must be positive")
    if not 0.0 <= y <= gap:
        raise ValueError("y must lie inside the channel")
    return lower_velocity + (upper_velocity - lower_velocity) * y / gap


def poiseuille_profile(
    y: float,
    *,
    gap: float,
    pressure_gradient: float,
    dynamic_viscosity: float,
) -> float:
    """Plane Poiseuille profile on y in [0, gap].

    pressure_gradient is dp/dx. A negative value produces positive flow.
    """
    if gap <= 0 or dynamic_viscosity <= 0:
        raise ValueError("gap and dynamic_viscosity must be positive")
    if not 0.0 <= y <= gap:
        raise ValueError("y must lie inside the channel")
    return -(pressure_gradient / (2.0 * dynamic_viscosity)) * y * (gap - y)


def poiseuille_mean_velocity(*, gap: float, pressure_gradient: float, dynamic_viscosity: float) -> float:
    if gap <= 0 or dynamic_viscosity <= 0:
        raise ValueError("gap and dynamic_viscosity must be positive")
    return -(pressure_gradient * gap * gap) / (12.0 * dynamic_viscosity)


def sine_diffusion_exact(x: float, time: float, diffusivity: float) -> float:
    if diffusivity < 0 or time < 0:
        raise ValueError("diffusivity and time must be non-negative")
    return sin(pi * x) * __import__("math").exp(-(pi * pi) * diffusivity * time)


def l2_error(values: Iterable[float], reference: Iterable[float]) -> float:
    pairs = list(zip(values, reference, strict=True))
    if not pairs:
        return 0.0
    return (sum((a - b) ** 2 for a, b in pairs) / len(pairs)) ** 0.5
