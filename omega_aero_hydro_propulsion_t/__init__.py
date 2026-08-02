"""Ω-AERO-HYDRO-PROPULSION-T: OAK-safe propulsion research kernels."""

from .analysis import RotorAnalysis, SectionResult, analyze_rotor
from .annular_bem import AnnularBEMAnalysis, AnnularSectionResult, analyze_annular_bem
from .cavitation import CavitationAssessment, assess_cavitation, cavitation_number
from .mission import (
    MissionGenome,
    MissionPhase,
    MissionPhaseResult,
    MissionReport,
    demo_air_mission,
    evaluate_mission,
)
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
from .polars import (
    PolarEvaluation,
    PolarRegistry,
    PolarSample,
    PolarTable,
    demo_polar_table,
)
from .r02_oak import R02OAKReport, run_r02_benchmarks

__all__ = [
    "AirfoilPolarConfig",
    "AnnularBEMAnalysis",
    "AnnularSectionResult",
    "BladeStation",
    "CavitationAssessment",
    "FluidMedium",
    "MissionGenome",
    "MissionPhase",
    "MissionPhaseResult",
    "MissionReport",
    "OperatingPoint",
    "OptimizationConstraints",
    "OptimizationReport",
    "PolarEvaluation",
    "PolarRegistry",
    "PolarSample",
    "PolarTable",
    "PropulsionOAKReport",
    "R02OAKReport",
    "RotorAnalysis",
    "RotorDesign",
    "SectionResult",
    "analyze_annular_bem",
    "analyze_rotor",
    "assess_cavitation",
    "cavitation_number",
    "default_air",
    "default_water",
    "demo_air_mission",
    "demo_polar_table",
    "demo_rotor",
    "evaluate_mission",
    "grid_optimize",
    "run_propulsion_benchmarks",
    "run_r02_benchmarks",
    "scale_rotor",
]

__version__ = "0.2.0"
