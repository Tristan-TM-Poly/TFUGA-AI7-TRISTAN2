from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class DimensionlessInput:
    density: float
    velocity: float
    length: float
    dynamic_viscosity: float
    sound_speed: float | None = None
    gravity: float | None = None
    surface_tension: float | None = None
    thermal_diffusivity: float | None = None
    mass_diffusivity: float | None = None
    kinematic_viscosity: float | None = None
    frequency: float | None = None
    mean_free_path: float | None = None
    relaxation_time: float | None = None

    def validate(self) -> None:
        positive = {
            "density": self.density,
            "length": self.length,
            "dynamic_viscosity": self.dynamic_viscosity,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        optional_positive = {
            "sound_speed": self.sound_speed,
            "gravity": self.gravity,
            "surface_tension": self.surface_tension,
            "thermal_diffusivity": self.thermal_diffusivity,
            "mass_diffusivity": self.mass_diffusivity,
            "kinematic_viscosity": self.kinematic_viscosity,
            "mean_free_path": self.mean_free_path,
            "relaxation_time": self.relaxation_time,
        }
        for name, value in optional_positive.items():
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when provided")


@dataclass(frozen=True)
class DimensionlessNumbers:
    reynolds: float
    mach: float | None = None
    froude: float | None = None
    weber: float | None = None
    capillary: float | None = None
    prandtl: float | None = None
    peclet_mass: float | None = None
    strouhal: float | None = None
    knudsen: float | None = None
    deborah: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_dimensionless(values: DimensionlessInput) -> DimensionlessNumbers:
    values.validate()
    rho = values.density
    speed = abs(values.velocity)
    length = values.length
    mu = values.dynamic_viscosity
    nu = values.kinematic_viscosity or mu / rho

    return DimensionlessNumbers(
        reynolds=rho * speed * length / mu,
        mach=None if values.sound_speed is None else speed / values.sound_speed,
        froude=None if values.gravity is None else speed / sqrt(values.gravity * length),
        weber=None if values.surface_tension is None else rho * speed * speed * length / values.surface_tension,
        capillary=None if values.surface_tension is None else mu * speed / values.surface_tension,
        prandtl=None if values.thermal_diffusivity is None else nu / values.thermal_diffusivity,
        peclet_mass=None if values.mass_diffusivity is None else speed * length / values.mass_diffusivity,
        strouhal=None if values.frequency is None else values.frequency * length / max(speed, 1e-300),
        knudsen=None if values.mean_free_path is None else values.mean_free_path / length,
        deborah=None if values.relaxation_time is None else values.relaxation_time * speed / length,
    )
