from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class FluidMedium:
    name: str
    density: float
    dynamic_viscosity: float
    sound_speed: float
    ambient_pressure: float = 101_325.0
    vapor_pressure: float | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("medium name cannot be empty")
        for field_name in ("density", "dynamic_viscosity", "sound_speed", "ambient_pressure"):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive")
        if self.vapor_pressure is not None:
            if self.vapor_pressure < 0:
                raise ValueError("vapor_pressure cannot be negative")
            if self.vapor_pressure >= self.ambient_pressure:
                raise ValueError("vapor_pressure must be below ambient_pressure")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BladeStation:
    radius: float
    chord: float
    twist_deg: float
    airfoil_id: str = "analytic-symmetric"

    def validate(self) -> None:
        if self.radius <= 0 or self.chord <= 0:
            raise ValueError("station radius and chord must be positive")
        if not self.airfoil_id.strip():
            raise ValueError("airfoil_id cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RotorDesign:
    name: str
    blade_count: int
    hub_radius: float
    tip_radius: float
    stations: tuple[BladeStation, ...]

    @classmethod
    def from_stations(
        cls,
        *,
        name: str,
        blade_count: int,
        hub_radius: float,
        tip_radius: float,
        stations: Iterable[BladeStation],
    ) -> "RotorDesign":
        return cls(name, blade_count, hub_radius, tip_radius, tuple(stations))

    @property
    def diameter(self) -> float:
        return 2.0 * self.tip_radius

    @property
    def disk_area(self) -> float:
        from math import pi

        return pi * (self.tip_radius**2 - self.hub_radius**2)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("rotor name cannot be empty")
        if self.blade_count < 1:
            raise ValueError("blade_count must be at least one")
        if self.hub_radius < 0 or self.tip_radius <= self.hub_radius:
            raise ValueError("tip_radius must exceed non-negative hub_radius")
        if len(self.stations) < 2:
            raise ValueError("at least two blade stations are required")
        radii = []
        for station in self.stations:
            station.validate()
            if not self.hub_radius <= station.radius <= self.tip_radius:
                raise ValueError("station radius must lie between hub and tip")
            radii.append(station.radius)
        if radii != sorted(radii) or len(set(radii)) != len(radii):
            raise ValueError("station radii must be strictly increasing")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "name": self.name,
            "blade_count": self.blade_count,
            "hub_radius": self.hub_radius,
            "tip_radius": self.tip_radius,
            "diameter": self.diameter,
            "disk_area": self.disk_area,
            "stations": [station.to_dict() for station in self.stations],
        }


@dataclass(frozen=True)
class OperatingPoint:
    freestream_velocity: float
    rpm: float
    collective_pitch_deg: float = 0.0

    def validate(self) -> None:
        if self.rpm < 0:
            raise ValueError("rpm cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AirfoilPolarConfig:
    lift_curve_slope_per_rad: float = 6.0
    zero_lift_alpha_deg: float = 0.0
    cd0: float = 0.012
    induced_drag_factor: float = 0.012
    stall_angle_deg: float = 15.0
    low_reynolds_reference: float = 100_000.0

    def validate(self) -> None:
        if self.lift_curve_slope_per_rad <= 0:
            raise ValueError("lift curve slope must be positive")
        if self.cd0 <= 0 or self.induced_drag_factor < 0:
            raise ValueError("drag parameters are invalid")
        if self.stall_angle_deg <= 0 or self.low_reynolds_reference <= 0:
            raise ValueError("stall angle and Reynolds reference must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_air() -> FluidMedium:
    return FluidMedium(
        name="air-isa-sea-level",
        density=1.225,
        dynamic_viscosity=1.81e-5,
        sound_speed=340.3,
        ambient_pressure=101_325.0,
    )


def default_water() -> FluidMedium:
    return FluidMedium(
        name="fresh-water-20c",
        density=998.2,
        dynamic_viscosity=1.002e-3,
        sound_speed=1482.0,
        ambient_pressure=101_325.0,
        vapor_pressure=2_339.0,
    )


def demo_rotor() -> RotorDesign:
    return RotorDesign.from_stations(
        name="oak-demo-three-blade",
        blade_count=3,
        hub_radius=0.10,
        tip_radius=0.60,
        stations=(
            BladeStation(0.10, 0.115, 34.0),
            BladeStation(0.22, 0.105, 27.0),
            BladeStation(0.36, 0.087, 20.0),
            BladeStation(0.49, 0.068, 14.5),
            BladeStation(0.60, 0.045, 10.0),
        ),
    )
