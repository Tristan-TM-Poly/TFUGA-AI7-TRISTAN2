"""Typed data models for Ω-SPACE-HG-T∞.

The module intentionally uses only the Python standard library so the research
kernel can run in constrained CI, classrooms and early mission-design studies.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class OrbitState:
    """Cartesian inertial state in SI units."""

    position_m: Vector3
    velocity_m_s: Vector3
    epoch_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SpacecraftConfig:
    """Reduced spacecraft configuration for coupled mission simulation."""

    name: str
    dry_mass_kg: float
    payload_mass_kg: float
    panel_area_m2: float
    panel_efficiency: float
    battery_capacity_wh: float
    initial_battery_fraction: float
    base_load_w: float
    payload_load_w: float
    downlink_load_w: float
    radiator_area_m2: float
    absorptivity: float = 0.35
    emissivity: float = 0.82
    thermal_capacity_j_k: float = 25_000.0
    initial_temperature_k: float = 293.15
    data_generation_mbps: float = 2.0
    storage_capacity_gb: float = 128.0
    downlink_rate_mbps: float = 40.0

    @property
    def wet_mass_kg(self) -> float:
        return self.dry_mass_kg + self.payload_mass_kg

    def validate(self) -> None:
        positive = {
            "dry_mass_kg": self.dry_mass_kg,
            "payload_mass_kg": self.payload_mass_kg,
            "panel_area_m2": self.panel_area_m2,
            "battery_capacity_wh": self.battery_capacity_wh,
            "thermal_capacity_j_k": self.thermal_capacity_j_k,
            "storage_capacity_gb": self.storage_capacity_gb,
        }
        for name, value in positive.items():
            if value <= 0.0:
                raise ValueError(f"{name} must be positive")
        bounded = {
            "panel_efficiency": self.panel_efficiency,
            "initial_battery_fraction": self.initial_battery_fraction,
            "absorptivity": self.absorptivity,
            "emissivity": self.emissivity,
        }
        for name, value in bounded.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissionConfig:
    """Mission-level inputs and explicit claim boundaries."""

    mission_id: str
    objective: str
    duration_s: float
    step_s: float
    central_body_mu_m3_s2: float
    central_body_radius_m: float
    orbit: OrbitState
    spacecraft: SpacecraftConfig
    payload_duty_cycle: float = 0.35
    downlink_duty_cycle: float = 0.12
    eclipse_fraction: float = 0.36
    solar_flux_w_m2: float = 1361.0
    albedo_flux_w_m2: float = 110.0
    deep_space_temperature_k: float = 3.0
    theorem_claimed: bool = False
    flight_qualified_claimed: bool = False
    scientific_validation_claimed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.spacecraft.validate()
        if self.duration_s <= 0 or self.step_s <= 0:
            raise ValueError("duration_s and step_s must be positive")
        if self.step_s > self.duration_s:
            raise ValueError("step_s cannot exceed duration_s")
        if self.central_body_mu_m3_s2 <= 0 or self.central_body_radius_m <= 0:
            raise ValueError("central-body parameters must be positive")
        for name, value in {
            "payload_duty_cycle": self.payload_duty_cycle,
            "downlink_duty_cycle": self.downlink_duty_cycle,
            "eclipse_fraction": self.eclipse_fraction,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.theorem_claimed or self.flight_qualified_claimed or self.scientific_validation_claimed:
            raise ValueError("R0.1 is research software and cannot assert proof or flight qualification")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["orbit"] = self.orbit.to_dict()
        payload["spacecraft"] = self.spacecraft.to_dict()
        return payload


@dataclass(frozen=True)
class SimulationPoint:
    time_s: float
    position_m: Vector3
    velocity_m_s: Vector3
    in_eclipse: bool
    generated_power_w: float
    load_power_w: float
    battery_wh: float
    temperature_k: float
    stored_data_gb: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissionMetrics:
    energy_drift_fraction: float
    minimum_battery_fraction: float
    maximum_battery_fraction: float
    minimum_temperature_k: float
    maximum_temperature_k: float
    maximum_stored_data_fraction: float
    completed_fraction: float
    safe: bool
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["violations"] = list(self.violations)
        return payload


@dataclass(frozen=True)
class MissionResult:
    config: MissionConfig
    points: tuple[SimulationPoint, ...]
    metrics: MissionMetrics
    hypergraph: dict[str, Any]

    def to_dict(self, include_points: bool = True) -> dict[str, Any]:
        payload = {
            "config": self.config.to_dict(),
            "metrics": self.metrics.to_dict(),
            "hypergraph": self.hypergraph,
        }
        if include_points:
            payload["points"] = [point.to_dict() for point in self.points]
        return payload


def require_finite(values: Iterable[float], label: str) -> None:
    """Reject NaN and infinity without importing a numerical dependency."""

    from math import isfinite

    if not all(isfinite(value) for value in values):
        raise ValueError(f"{label} contains a non-finite value")
