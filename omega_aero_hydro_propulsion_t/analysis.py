from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, atan2, cos, exp, inf, pi, sin, sqrt
from typing import Any

from .airfoil import analytic_polar
from .models import AirfoilPolarConfig, FluidMedium, OperatingPoint, RotorDesign


@dataclass(frozen=True)
class SectionResult:
    radius: float
    width: float
    chord: float
    twist_deg: float
    inflow_angle_deg: float
    angle_of_attack_deg: float
    relative_speed: float
    reynolds: float
    mach: float
    lift_coefficient: float
    drag_coefficient: float
    tip_loss_factor: float
    thrust: float
    torque: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RotorAnalysis:
    design_name: str
    medium_name: str
    operating_point: OperatingPoint
    thrust: float
    torque: float
    shaft_power: float
    propulsive_efficiency: float
    advance_ratio: float
    thrust_coefficient: float
    torque_coefficient: float
    power_coefficient: float
    induced_velocity: float
    tip_speed: float
    tip_mach: float
    converged: bool
    iterations: int
    residual: float
    sections: tuple[SectionResult, ...]
    model: str = "blade-element-uniform-induction-r0.1"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operating_point"] = self.operating_point.to_dict()
        payload["sections"] = [section.to_dict() for section in self.sections]
        return payload


def _tip_loss(blades: int, radius: float, tip_radius: float, phi: float) -> float:
    sin_phi = max(abs(sin(phi)), 1e-8)
    exponent = -(blades / 2.0) * (tip_radius - radius) / max(radius * sin_phi, 1e-12)
    return max(0.05, min(1.0, 2.0 * acos(min(1.0, exp(exponent))) / pi))


def _single_pass(
    design: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    induced_velocity: float,
    polar: AirfoilPolarConfig,
) -> tuple[float, float, tuple[SectionResult, ...]]:
    omega = operating.rpm * 2.0 * pi / 60.0
    axial_speed = operating.freestream_velocity + induced_velocity
    total_thrust = 0.0
    total_torque = 0.0
    sections: list[SectionResult] = []

    for left, right in zip(design.stations, design.stations[1:]):
        radius = 0.5 * (left.radius + right.radius)
        width = right.radius - left.radius
        chord = 0.5 * (left.chord + right.chord)
        twist_deg = 0.5 * (left.twist_deg + right.twist_deg) + operating.collective_pitch_deg
        tangential_speed = omega * radius
        relative_speed = sqrt(axial_speed * axial_speed + tangential_speed * tangential_speed)
        if relative_speed <= 1e-15 or omega <= 1e-15:
            phi = 0.0
            alpha_deg = 0.0
            reynolds = 1.0
            mach = 0.0
            cl = 0.0
            cd = 0.0
            loss = 1.0
            d_thrust = 0.0
            d_torque = 0.0
        else:
            phi = atan2(axial_speed, tangential_speed)
            alpha_deg = twist_deg - phi * 180.0 / pi
            reynolds = medium.density * relative_speed * chord / medium.dynamic_viscosity
            mach = relative_speed / medium.sound_speed
            point = analytic_polar(alpha_deg, reynolds=reynolds, mach=mach, config=polar)
            cl = point.lift_coefficient
            cd = point.drag_coefficient
            loss = _tip_loss(design.blade_count, radius, design.tip_radius, phi)
            dynamic_force = 0.5 * medium.density * relative_speed**2 * chord * width * design.blade_count * loss
            axial_coefficient = cl * cos(phi) - cd * sin(phi)
            tangential_coefficient = cl * sin(phi) + cd * cos(phi)
            d_thrust = dynamic_force * axial_coefficient
            d_torque = dynamic_force * tangential_coefficient * radius

        total_thrust += d_thrust
        total_torque += d_torque
        sections.append(
            SectionResult(
                radius=radius,
                width=width,
                chord=chord,
                twist_deg=twist_deg,
                inflow_angle_deg=phi * 180.0 / pi,
                angle_of_attack_deg=alpha_deg,
                relative_speed=relative_speed,
                reynolds=reynolds,
                mach=mach,
                lift_coefficient=cl,
                drag_coefficient=cd,
                tip_loss_factor=loss,
                thrust=d_thrust,
                torque=d_torque,
            )
        )
    return total_thrust, total_torque, tuple(sections)


def analyze_rotor(
    design: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    *,
    polar: AirfoilPolarConfig | None = None,
    max_iterations: int = 80,
    tolerance: float = 1e-7,
    relaxation: float = 0.35,
) -> RotorAnalysis:
    """Analyze a rotor with blade elements and uniform actuator-disk induction.

    The model is suitable for screening, education and regression tests. It is
    not a certified CFD, aeroelastic or cavitation model.
    """
    design.validate()
    medium.validate()
    operating.validate()
    cfg = polar or AirfoilPolarConfig()
    cfg.validate()
    if max_iterations < 0 or tolerance <= 0 or not 0 < relaxation <= 1:
        raise ValueError("invalid iteration controls")

    omega = operating.rpm * 2.0 * pi / 60.0
    if omega <= 1e-15:
        thrust, torque, sections = _single_pass(design, medium, operating, 0.0, cfg)
        return RotorAnalysis(
            design.name,
            medium.name,
            operating,
            thrust,
            torque,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            True,
            0,
            0.0,
            sections,
        )

    induced = 0.0
    converged = max_iterations == 0
    residual = inf if max_iterations else 0.0
    iterations = 0
    sections: tuple[SectionResult, ...] = ()
    thrust = torque = 0.0

    passes = max(1, max_iterations)
    for iteration in range(passes):
        thrust, torque, sections = _single_pass(design, medium, operating, induced, cfg)
        if max_iterations == 0:
            break
        target = 0.0
        if thrust > 0:
            target = 0.5 * (
                -operating.freestream_velocity
                + sqrt(operating.freestream_velocity**2 + 2.0 * thrust / (medium.density * design.disk_area))
            )
        updated = (1.0 - relaxation) * induced + relaxation * target
        residual = abs(updated - induced) / max(1.0, abs(updated))
        induced = updated
        iterations = iteration + 1
        if residual <= tolerance:
            converged = True
            thrust, torque, sections = _single_pass(design, medium, operating, induced, cfg)
            break

    shaft_power = torque * omega
    useful_power = max(0.0, thrust * operating.freestream_velocity)
    efficiency = useful_power / shaft_power if shaft_power > 0 else 0.0
    n = operating.rpm / 60.0
    diameter = design.diameter
    if n > 0:
        advance_ratio = operating.freestream_velocity / (n * diameter)
        thrust_coefficient = thrust / (medium.density * n**2 * diameter**4)
        torque_coefficient = torque / (medium.density * n**2 * diameter**5)
        power_coefficient = shaft_power / (medium.density * n**3 * diameter**5)
    else:
        advance_ratio = thrust_coefficient = torque_coefficient = power_coefficient = 0.0
    tip_speed = sqrt((omega * design.tip_radius) ** 2 + (operating.freestream_velocity + induced) ** 2)

    return RotorAnalysis(
        design_name=design.name,
        medium_name=medium.name,
        operating_point=operating,
        thrust=thrust,
        torque=torque,
        shaft_power=shaft_power,
        propulsive_efficiency=efficiency,
        advance_ratio=advance_ratio,
        thrust_coefficient=thrust_coefficient,
        torque_coefficient=torque_coefficient,
        power_coefficient=power_coefficient,
        induced_velocity=induced,
        tip_speed=tip_speed,
        tip_mach=tip_speed / medium.sound_speed,
        converged=converged,
        iterations=iterations,
        residual=residual,
        sections=sections,
    )
