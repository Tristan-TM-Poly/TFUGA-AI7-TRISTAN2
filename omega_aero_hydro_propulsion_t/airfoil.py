from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi, tanh
from typing import Any

from .models import AirfoilPolarConfig


@dataclass(frozen=True)
class PolarPoint:
    alpha_deg: float
    reynolds: float
    mach: float
    lift_coefficient: float
    drag_coefficient: float
    model: str = "analytic-low-order"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analytic_polar(
    alpha_deg: float,
    *,
    reynolds: float,
    mach: float,
    config: AirfoilPolarConfig | None = None,
) -> PolarPoint:
    """Smooth low-order polar for screening and deterministic tests.

    This is not a replacement for measured or CFD-derived airfoil polars.
    """
    cfg = config or AirfoilPolarConfig()
    cfg.validate()
    if reynolds <= 0:
        raise ValueError("reynolds must be positive")
    if mach < 0:
        raise ValueError("mach cannot be negative")

    alpha_rad = (alpha_deg - cfg.zero_lift_alpha_deg) * pi / 180.0
    linear_cl = cfg.lift_curve_slope_per_rad * alpha_rad
    stall_cl = cfg.lift_curve_slope_per_rad * cfg.stall_angle_deg * pi / 180.0
    cl = stall_cl * tanh(linear_cl / stall_cl)

    low_re_penalty = 1.0
    if reynolds < cfg.low_reynolds_reference:
        low_re_penalty += 0.35 * ((cfg.low_reynolds_reference / reynolds) ** 0.5 - 1.0)
    transonic_penalty = 1.0 + max(0.0, mach - 0.70) ** 2 * 8.0
    cd = (cfg.cd0 * low_re_penalty + cfg.induced_drag_factor * cl * cl) * transonic_penalty

    return PolarPoint(
        alpha_deg=alpha_deg,
        reynolds=reynolds,
        mach=mach,
        lift_coefficient=cl,
        drag_coefficient=cd,
    )
