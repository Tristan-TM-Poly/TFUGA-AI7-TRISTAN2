from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, atan2, cos, exp, inf, pi, sin, sqrt
from typing import Any

from .airfoil import analytic_polar
from .models import AirfoilPolarConfig, FluidMedium, OperatingPoint, RotorDesign
from .polars import PolarRegistry


@dataclass(frozen=True)
class AnnularSectionResult:
    radius: float
    width: float
    chord: float
    twist_deg: float
    airfoil_id: str
    inflow_angle_deg: float
    angle_of_attack_deg: float
    relative_speed: float
    reynolds: float
    mach: float
    lift_coefficient: float
    drag_coefficient: float
    axial_induced_velocity: float
    tangential_induction_factor: float
    tip_hub_loss_factor: float
    solidity: float
    thrust: float
    torque: float
    iterations: int
    residual: float
    converged: bool
    polar_model: str
    polar_extrapolated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnnularBEMAnalysis:
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
    tip_speed: float
    tip_mach: float
    converged: bool
    maximum_section_residual: float
    sections: tuple[AnnularSectionResult, ...]
    model: str = "annular-bem-propeller-momentum-r0.2"
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operating_point"] = self.operating_point.to_dict()
        payload["sections"] = [section.to_dict() for section in self.sections]
        return payload


def _loss_factor(blades: int, hub_radius: float, tip_radius: float, radius: float, phi: float) -> float:
    sin_phi = max(abs(sin(phi)), 1e-8)
    tip_argument = (blades / 2.0) * max(0.0, tip_radius - radius) / max(radius * sin_phi, 1e-12)
    hub_argument = (blades / 2.0) * max(0.0, radius - hub_radius) / max(hub_radius * sin_phi, 1e-12)
    tip = 2.0 * acos(min(1.0, exp(-tip_argument))) / pi
    hub = 1.0 if hub_radius <= 1e-12 else 2.0 * acos(min(1.0, exp(-hub_argument))) / pi
    return max(0.03, min(1.0, tip * hub))


def _polar_values(
    airfoil_id: str,
    alpha_deg: float,
    reynolds: float,
    mach: float,
    registry: PolarRegistry | None,
    analytic_config: AirfoilPolarConfig,
) -> tuple[float, float, str, bool]:
    if registry is not None and registry.contains(airfoil_id):
        point = registry.evaluate(airfoil_id, alpha_deg, reynolds=reynolds, mach=mach)
        return (
            point.lift_coefficient,
            point.drag_coefficient,
            point.model,
            point.alpha_extrapolated or point.condition_extrapolated,
        )
    point = analytic_polar(alpha_deg, reynolds=reynolds, mach=mach, config=analytic_config)
    return point.lift_coefficient, point.drag_coefficient, point.model, False


def _solve_annulus(
    design: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    *,
    radius: float,
    width: float,
    chord: float,
    twist_deg: float,
    airfoil_id: str,
    registry: PolarRegistry | None,
    analytic_config: AirfoilPolarConfig,
    max_iterations: int,
    tolerance: float,
    relaxation: float,
) -> AnnularSectionResult:
    omega = operating.rpm * 2.0 * pi / 60.0
    solidity = design.blade_count * chord / (2.0 * pi * radius)
    if omega <= 1e-15:
        return AnnularSectionResult(
            radius=radius,
            width=width,
            chord=chord,
            twist_deg=twist_deg,
            airfoil_id=airfoil_id,
            inflow_angle_deg=0.0,
            angle_of_attack_deg=0.0,
            relative_speed=0.0,
            reynolds=1.0,
            mach=0.0,
            lift_coefficient=0.0,
            drag_coefficient=0.0,
            axial_induced_velocity=0.0,
            tangential_induction_factor=0.0,
            tip_hub_loss_factor=1.0,
            solidity=solidity,
            thrust=0.0,
            torque=0.0,
            iterations=0,
            residual=0.0,
            converged=True,
            polar_model="stationary",
            polar_extrapolated=False,
        )

    axial_induced = 0.02 * omega * design.tip_radius
    tangential_factor = 0.0
    residual = inf
    converged = False
    polar_model = "unknown"
    polar_extrapolated = False
    iterations = 0

    for iteration in range(max_iterations):
        axial_speed = operating.freestream_velocity + axial_induced
        tangential_speed = omega * radius * (1.0 - tangential_factor)
        relative_speed = sqrt(axial_speed**2 + tangential_speed**2)
        phi = atan2(axial_speed, max(tangential_speed, 1e-12))
        alpha_deg = twist_deg - phi * 180.0 / pi
        reynolds = max(1.0, medium.density * relative_speed * chord / medium.dynamic_viscosity)
        mach = relative_speed / medium.sound_speed
        cl, cd, polar_model, polar_extrapolated = _polar_values(
            airfoil_id, alpha_deg, reynolds, mach, registry, analytic_config
        )
        loss = _loss_factor(design.blade_count, design.hub_radius, design.tip_radius, radius, phi)
        dynamic_force = 0.5 * medium.density * relative_speed**2 * chord * width * design.blade_count * loss
        normal_coefficient = cl * cos(phi) - cd * sin(phi)
        tangential_coefficient = cl * sin(phi) + cd * cos(phi)
        d_thrust = dynamic_force * normal_coefficient
        d_torque = dynamic_force * tangential_coefficient * radius

        denominator = 4.0 * pi * medium.density * radius * width * loss
        momentum_load = max(0.0, d_thrust) / max(denominator, 1e-15)
        freestream = operating.freestream_velocity
        target_axial = 0.5 * (-freestream + sqrt(max(0.0, freestream**2 + 4.0 * momentum_load)))
        axial_through = max(abs(freestream + target_axial), 1e-8)
        target_tangential = d_torque / max(
            4.0 * pi * medium.density * radius**3 * width * loss * axial_through * omega,
            1e-15,
        )
        target_tangential = max(-0.30, min(0.90, target_tangential))
        updated_axial = (1.0 - relaxation) * axial_induced + relaxation * target_axial
        updated_tangential = (1.0 - relaxation) * tangential_factor + relaxation * target_tangential
        axial_residual = abs(updated_axial - axial_induced) / max(1.0, abs(updated_axial))
        tangential_residual = abs(updated_tangential - tangential_factor)
        residual = max(axial_residual, tangential_residual)
        axial_induced = updated_axial
        tangential_factor = updated_tangential
        iterations = iteration + 1
        if residual <= tolerance:
            converged = True
            break

    axial_speed = operating.freestream_velocity + axial_induced
    tangential_speed = omega * radius * (1.0 - tangential_factor)
    relative_speed = sqrt(axial_speed**2 + tangential_speed**2)
    phi = atan2(axial_speed, max(tangential_speed, 1e-12))
    alpha_deg = twist_deg - phi * 180.0 / pi
    reynolds = max(1.0, medium.density * relative_speed * chord / medium.dynamic_viscosity)
    mach = relative_speed / medium.sound_speed
    cl, cd, polar_model, polar_extrapolated = _polar_values(
        airfoil_id, alpha_deg, reynolds, mach, registry, analytic_config
    )
    loss = _loss_factor(design.blade_count, design.hub_radius, design.tip_radius, radius, phi)
    dynamic_force = 0.5 * medium.density * relative_speed**2 * chord * width * design.blade_count * loss
    d_thrust = dynamic_force * (cl * cos(phi) - cd * sin(phi))
    d_torque = dynamic_force * (cl * sin(phi) + cd * cos(phi)) * radius

    return AnnularSectionResult(
        radius=radius,
        width=width,
        chord=chord,
        twist_deg=twist_deg,
        airfoil_id=airfoil_id,
        inflow_angle_deg=phi * 180.0 / pi,
        angle_of_attack_deg=alpha_deg,
        relative_speed=relative_speed,
        reynolds=reynolds,
        mach=mach,
        lift_coefficient=cl,
        drag_coefficient=cd,
        axial_induced_velocity=axial_induced,
        tangential_induction_factor=tangential_factor,
        tip_hub_loss_factor=loss,
        solidity=solidity,
        thrust=d_thrust,
        torque=d_torque,
        iterations=iterations,
        residual=residual,
        converged=converged,
        polar_model=polar_model,
        polar_extrapolated=polar_extrapolated,
    )


def analyze_annular_bem(
    design: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    *,
    registry: PolarRegistry | None = None,
    analytic_config: AirfoilPolarConfig | None = None,
    max_iterations: int = 160,
    tolerance: float = 1e-6,
    relaxation: float = 0.25,
) -> AnnularBEMAnalysis:
    """Annular propeller BEM with local axial and tangential induction.

    This deterministic research model is not a replacement for validated
    free-wake, CFD, FSI, acoustic or experimental evidence.
    """
    design.validate()
    medium.validate()
    operating.validate()
    config = analytic_config or AirfoilPolarConfig()
    config.validate()
    if max_iterations < 1 or tolerance <= 0 or not 0.0 < relaxation <= 1.0:
        raise ValueError("invalid annular iteration controls")

    sections: list[AnnularSectionResult] = []
    for left, right in zip(design.stations, design.stations[1:]):
        sections.append(
            _solve_annulus(
                design,
                medium,
                operating,
                radius=0.5 * (left.radius + right.radius),
                width=right.radius - left.radius,
                chord=0.5 * (left.chord + right.chord),
                twist_deg=0.5 * (left.twist_deg + right.twist_deg) + operating.collective_pitch_deg,
                airfoil_id=left.airfoil_id,
                registry=registry,
                analytic_config=config,
                max_iterations=max_iterations,
                tolerance=tolerance,
                relaxation=relaxation,
            )
        )

    thrust = sum(section.thrust for section in sections)
    torque = sum(section.torque for section in sections)
    omega = operating.rpm * 2.0 * pi / 60.0
    shaft_power = torque * omega
    efficiency = max(0.0, thrust * operating.freestream_velocity) / shaft_power if shaft_power > 0 else 0.0
    n = operating.rpm / 60.0
    diameter = design.diameter
    if n > 0:
        advance_ratio = operating.freestream_velocity / (n * diameter)
        thrust_coefficient = thrust / (medium.density * n**2 * diameter**4)
        torque_coefficient = torque / (medium.density * n**2 * diameter**5)
        power_coefficient = shaft_power / (medium.density * n**3 * diameter**5)
    else:
        advance_ratio = thrust_coefficient = torque_coefficient = power_coefficient = 0.0
    maximum_axial = max((section.axial_induced_velocity for section in sections), default=0.0)
    tip_speed = sqrt((omega * design.tip_radius) ** 2 + (operating.freestream_velocity + maximum_axial) ** 2)
    maximum_residual = max((section.residual for section in sections), default=0.0)
    return AnnularBEMAnalysis(
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
        tip_speed=tip_speed,
        tip_mach=tip_speed / medium.sound_speed,
        converged=all(section.converged for section in sections),
        maximum_section_residual=maximum_residual,
        sections=tuple(sections),
    )
