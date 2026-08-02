from __future__ import annotations

from dataclasses import asdict, dataclass
from math import inf
from typing import Any

from .analysis import RotorAnalysis
from .models import FluidMedium


@dataclass(frozen=True)
class CavitationAssessment:
    applicable: bool
    minimum_cavitation_number: float | None
    minimum_margin: float | None
    risk: bool
    pressure_coefficient_model: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def cavitation_number(
    *,
    ambient_pressure: float,
    vapor_pressure: float,
    density: float,
    speed: float,
) -> float:
    if ambient_pressure <= vapor_pressure:
        raise ValueError("ambient pressure must exceed vapor pressure")
    if density <= 0 or speed < 0:
        raise ValueError("density must be positive and speed non-negative")
    if speed == 0:
        return inf
    return (ambient_pressure - vapor_pressure) / (0.5 * density * speed * speed)


def assess_cavitation(analysis: RotorAnalysis, medium: FluidMedium) -> CavitationAssessment:
    """Heuristic screening gate, not a resolved pressure-field calculation."""
    medium.validate()
    if medium.vapor_pressure is None:
        return CavitationAssessment(False, None, None, False, "not-applicable")

    minimum_sigma = inf
    minimum_margin = inf
    for section in analysis.sections:
        sigma = cavitation_number(
            ambient_pressure=medium.ambient_pressure,
            vapor_pressure=medium.vapor_pressure,
            density=medium.density,
            speed=section.relative_speed,
        )
        # Conservative screening surrogate; replace with validated sectional Cp data.
        cp_min_estimate = -max(0.25, 1.15 * abs(section.lift_coefficient) + 0.5 * section.drag_coefficient)
        margin = sigma + cp_min_estimate
        minimum_sigma = min(minimum_sigma, sigma)
        minimum_margin = min(minimum_margin, margin)

    return CavitationAssessment(
        applicable=True,
        minimum_cavitation_number=minimum_sigma,
        minimum_margin=minimum_margin,
        risk=minimum_margin <= 0.0,
        pressure_coefficient_model="heuristic-cp-min-screening-r0.1",
    )
