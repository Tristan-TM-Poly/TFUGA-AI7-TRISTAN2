from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi, sqrt
from typing import Any

from .annular_bem import AnnularBEMAnalysis
from .models import OperatingPoint, RotorDesign


@dataclass(frozen=True)
class BladeMaterial:
    name: str
    density: float
    young_modulus: float
    allowable_stress: float
    fatigue_strength: float | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("material name cannot be empty")
        for field_name in ("density", "young_modulus", "allowable_stress"):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive")
        if self.fatigue_strength is not None and self.fatigue_strength <= 0:
            raise ValueError("fatigue_strength must be positive when provided")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralAssumptions:
    thickness_ratio: float = 0.14
    effective_area_fraction: float = 0.22
    effective_inertia_fraction: float = 0.16
    aerodynamic_load_factor: float = 1.5
    centrifugal_load_factor: float = 1.2
    minimum_safety_factor: float = 1.5
    maximum_tip_deflection_fraction: float = 0.10

    def validate(self) -> None:
        fractions = (
            self.thickness_ratio,
            self.effective_area_fraction,
            self.effective_inertia_fraction,
            self.maximum_tip_deflection_fraction,
        )
        if any(value <= 0 for value in fractions):
            raise ValueError("structural fractions must be positive")
        if self.thickness_ratio >= 1 or self.maximum_tip_deflection_fraction >= 1:
            raise ValueError("thickness and deflection fractions must be below one")
        if self.aerodynamic_load_factor < 1 or self.centrifugal_load_factor < 1:
            raise ValueError("load factors must be at least one")
        if self.minimum_safety_factor <= 0:
            raise ValueError("minimum_safety_factor must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralSectionResult:
    radius: float
    width: float
    chord: float
    thickness: float
    estimated_mass_per_blade: float
    centrifugal_force: float
    bending_moment: float
    torsional_moment: float
    normal_stress: float
    shear_stress: float
    von_mises_stress: float
    strain: float
    safety_factor: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralBladeReport:
    design_name: str
    material: BladeMaterial
    operating_point: OperatingPoint
    rotor_mass: float
    maximum_von_mises_stress: float
    maximum_strain: float
    minimum_safety_factor: float
    estimated_tip_deflection: float
    tip_deflection_fraction: float
    feasible: bool
    violations: tuple[str, ...]
    sections: tuple[StructuralSectionResult, ...]
    model: str = "low-order-rotating-beam-screen-r0.3"
    physics_certified: bool = False
    certification_notice: str = "screening only; requires validated laminate/section properties, FEA, fatigue, modal, flutter and test evidence"

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_name": self.design_name,
            "material": self.material.to_dict(),
            "operating_point": self.operating_point.to_dict(),
            "rotor_mass": self.rotor_mass,
            "maximum_von_mises_stress": self.maximum_von_mises_stress,
            "maximum_strain": self.maximum_strain,
            "minimum_safety_factor": self.minimum_safety_factor,
            "estimated_tip_deflection": self.estimated_tip_deflection,
            "tip_deflection_fraction": self.tip_deflection_fraction,
            "feasible": self.feasible,
            "violations": list(self.violations),
            "sections": [section.to_dict() for section in self.sections],
            "model": self.model,
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def default_composite_material() -> BladeMaterial:
    return BladeMaterial("generic-carbon-epoxy-screening", 1600.0, 70.0e9, 450.0e6, 220.0e6)


def analyze_blade_structure(
    design: RotorDesign,
    operating: OperatingPoint,
    aerodynamic: AnnularBEMAnalysis,
    *,
    material: BladeMaterial | None = None,
    assumptions: StructuralAssumptions | None = None,
) -> StructuralBladeReport:
    design.validate()
    operating.validate()
    mat = material or default_composite_material()
    cfg = assumptions or StructuralAssumptions()
    mat.validate()
    cfg.validate()
    if aerodynamic.design_name != design.name:
        raise ValueError("aerodynamic analysis and structural design names differ")
    if len(aerodynamic.sections) != len(design.stations) - 1:
        raise ValueError("aerodynamic sections do not match rotor station intervals")

    omega = operating.rpm * 2.0 * pi / 60.0
    intervals: list[dict[str, float]] = []
    for aero in aerodynamic.sections:
        thickness = cfg.thickness_ratio * aero.chord
        effective_area = aero.chord * thickness * cfg.effective_area_fraction
        effective_inertia = aero.chord * thickness**3 / 12.0 * cfg.effective_inertia_fraction
        intervals.append({
            "radius": aero.radius,
            "width": aero.width,
            "chord": aero.chord,
            "thickness": thickness,
            "area": effective_area,
            "inertia": effective_inertia,
            "section_modulus": effective_inertia / max(0.5 * thickness, 1e-15),
            "mass": mat.density * effective_area * aero.width,
            "thrust_per_blade": aero.thrust / design.blade_count,
            "torque_per_blade": aero.torque / design.blade_count,
        })

    results: list[StructuralSectionResult] = []
    for index, current in enumerate(intervals):
        outward = intervals[index:]
        centrifugal_force = cfg.centrifugal_load_factor * sum(item["mass"] * omega**2 * item["radius"] for item in outward)
        bending_moment = cfg.aerodynamic_load_factor * sum(item["thrust_per_blade"] * max(0.0, item["radius"] - current["radius"]) for item in outward)
        torsional_moment = cfg.aerodynamic_load_factor * sum(item["torque_per_blade"] for item in outward)
        normal_stress = centrifugal_force / max(current["area"], 1e-15) + abs(bending_moment) / max(current["section_modulus"], 1e-15)
        shear_stress = abs(torsional_moment) * current["thickness"] / max(2.0 * current["inertia"], 1e-15)
        von_mises = sqrt(normal_stress**2 + 3.0 * shear_stress**2)
        results.append(StructuralSectionResult(
            radius=current["radius"], width=current["width"], chord=current["chord"], thickness=current["thickness"],
            estimated_mass_per_blade=current["mass"], centrifugal_force=centrifugal_force,
            bending_moment=bending_moment, torsional_moment=torsional_moment,
            normal_stress=normal_stress, shear_stress=shear_stress,
            von_mises_stress=von_mises, strain=von_mises / mat.young_modulus,
            safety_factor=mat.allowable_stress / max(von_mises, 1e-15),
        ))

    rotor_mass = design.blade_count * sum(item["mass"] for item in intervals)
    maximum_stress = max(item.von_mises_stress for item in results)
    minimum_safety = min(item.safety_factor for item in results)
    span = design.tip_radius - design.hub_radius
    total_flap_load = cfg.aerodynamic_load_factor * sum(abs(item["thrust_per_blade"]) for item in intervals)
    estimated_tip_deflection = total_flap_load * span**3 / max(3.0 * mat.young_modulus * intervals[0]["inertia"], 1e-15)
    tip_deflection_fraction = estimated_tip_deflection / max(span, 1e-15)
    violations: list[str] = []
    if minimum_safety < cfg.minimum_safety_factor:
        violations.append("minimum_safety_factor")
    if tip_deflection_fraction > cfg.maximum_tip_deflection_fraction:
        violations.append("maximum_tip_deflection")
    if mat.fatigue_strength is not None and maximum_stress > mat.fatigue_strength:
        violations.append("fatigue_strength_screen")
    if aerodynamic.tip_mach >= 1.0:
        violations.append("transonic_or_supersonic_tip_requires_higher_fidelity")
    if not aerodynamic.converged:
        violations.append("aerodynamic_input_not_converged")
    return StructuralBladeReport(
        design.name, mat, operating, rotor_mass, maximum_stress,
        max(item.strain for item in results), minimum_safety, estimated_tip_deflection,
        tip_deflection_fraction, not violations, tuple(violations), tuple(results)
    )
