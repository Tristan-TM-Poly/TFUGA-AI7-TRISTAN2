"""Ω-AERO-HYDRO-PROPULSION-T: OAK-safe low-order rotor design kernel."""

from .analysis import RotorAnalysis, SectionResult, analyze_rotor
from .cavitation import CavitationAssessment, assess_cavitation, cavitation_number
from .models import (
    AirfoilPolarConfig,
    BladeStation,
    FluidMedium,
    OperatingPoint,
    RotorDesign,
    default_air,
    default_water,
    demo_rotor,
)
from .oak import PropulsionOAKReport, run_propulsion_benchmarks
from .optimizer import OptimizationConstraints, OptimizationReport, grid_optimize, scale_rotor

__all__ = [
    "AirfoilPolarConfig",
    "BladeStation",
    "CavitationAssessment",
    "FluidMedium",
    "OperatingPoint",
    "OptimizationConstraints",
    "OptimizationReport",
    "PropulsionOAKReport",
    "RotorAnalysis",
    "RotorDesign",
    "SectionResult",
    "analyze_rotor",
    "assess_cavitation",
    "cavitation_number",
    "default_air",
    "default_water",
    "demo_rotor",
    "grid_optimize",
    "run_propulsion_benchmarks",
    "scale_rotor",
]

__version__ = "0.1.0"
