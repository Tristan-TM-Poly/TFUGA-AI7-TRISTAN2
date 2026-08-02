from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log10
from typing import Any

from .annular_bem import AnnularBEMAnalysis
from .models import OperatingPoint, RotorDesign


@dataclass(frozen=True)
class AcousticLimits:
    maximum_overall_spl_db: float | None = None
    maximum_tip_mach: float | None = 0.85
    maximum_blade_passing_frequency_hz: float | None = None

    def validate(self) -> None:
        for name, value in (
            ("maximum_overall_spl_db", self.maximum_overall_spl_db),
            ("maximum_tip_mach", self.maximum_tip_mach),
            ("maximum_blade_passing_frequency_hz", self.maximum_blade_passing_frequency_hz),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when provided")


@dataclass(frozen=True)
class AcousticHarmonic:
    order: int
    frequency_hz: float
    estimated_level_db: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AcousticScreenReport:
    design_name: str
    observer_distance_m: float
    rotational_frequency_hz: float
    blade_passing_frequency_hz: float
    source_level_at_1m_db: float
    estimated_overall_spl_db: float
    tip_mach: float
    loading_noise_index: float
    harmonics: tuple[AcousticHarmonic, ...]
    feasible: bool
    violations: tuple[str, ...]
    model: str = "dimensionless-tonal-acoustic-screen-r0.3"
    physics_certified: bool = False
    certification_notice: str = "screening proxy only; not a FW-H, CFD-acoustic, psychoacoustic or certified measurement result"

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_name": self.design_name,
            "observer_distance_m": self.observer_distance_m,
            "rotational_frequency_hz": self.rotational_frequency_hz,
            "blade_passing_frequency_hz": self.blade_passing_frequency_hz,
            "source_level_at_1m_db": self.source_level_at_1m_db,
            "estimated_overall_spl_db": self.estimated_overall_spl_db,
            "tip_mach": self.tip_mach,
            "loading_noise_index": self.loading_noise_index,
            "harmonics": [item.to_dict() for item in self.harmonics],
            "feasible": self.feasible,
            "violations": list(self.violations),
            "model": self.model,
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def screen_rotor_acoustics(
    design: RotorDesign,
    operating: OperatingPoint,
    aerodynamic: AnnularBEMAnalysis,
    *,
    observer_distance_m: float = 10.0,
    limits: AcousticLimits | None = None,
    harmonic_count: int = 6,
) -> AcousticScreenReport:
    design.validate()
    operating.validate()
    cfg = limits or AcousticLimits()
    cfg.validate()
    if observer_distance_m <= 0:
        raise ValueError("observer_distance_m must be positive")
    if harmonic_count < 1:
        raise ValueError("harmonic_count must be at least one")
    if aerodynamic.design_name != design.name:
        raise ValueError("aerodynamic analysis and acoustic design names differ")
    rotational_frequency = operating.rpm / 60.0
    blade_passing_frequency = rotational_frequency * design.blade_count
    loading_index = abs(aerodynamic.thrust_coefficient) * max(aerodynamic.tip_mach, 1e-6) ** 5
    source_level = (
        82.0
        + 10.0 * log10(max(design.blade_count, 1))
        + 20.0 * log10(max(abs(aerodynamic.thrust_coefficient), 1e-6) / 0.05)
        + 50.0 * log10(max(aerodynamic.tip_mach, 0.03) / 0.30)
    )
    overall = source_level - 20.0 * log10(max(observer_distance_m, 1e-12))
    harmonics = tuple(
        AcousticHarmonic(order, blade_passing_frequency * order, overall - 6.0 * log10(order))
        for order in range(1, harmonic_count + 1)
    )
    violations: list[str] = []
    if cfg.maximum_overall_spl_db is not None and overall > cfg.maximum_overall_spl_db:
        violations.append("maximum_overall_spl_db")
    if cfg.maximum_tip_mach is not None and aerodynamic.tip_mach > cfg.maximum_tip_mach:
        violations.append("maximum_tip_mach")
    if cfg.maximum_blade_passing_frequency_hz is not None and blade_passing_frequency > cfg.maximum_blade_passing_frequency_hz:
        violations.append("maximum_blade_passing_frequency_hz")
    if not aerodynamic.converged:
        violations.append("aerodynamic_input_not_converged")
    return AcousticScreenReport(
        design.name, observer_distance_m, rotational_frequency, blade_passing_frequency,
        source_level, overall, aerodynamic.tip_mach, loading_index, harmonics,
        not violations, tuple(violations)
    )
