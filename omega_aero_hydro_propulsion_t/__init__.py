"""Ω-AERO-HYDRO-PROPULSION-T: OAK-safe propulsion research kernels."""

from .acoustics import AcousticHarmonic, AcousticLimits, AcousticScreenReport, screen_rotor_acoustics
from .analysis import RotorAnalysis, SectionResult, analyze_rotor
from .annular_bem import AnnularBEMAnalysis, AnnularSectionResult, analyze_annular_bem
from .cavitation import CavitationAssessment, assess_cavitation, cavitation_number
from .faults import FaultCaseResult, FaultEnvelopeReport, FaultPhaseResult, FaultScenario, default_fault_scenarios, evaluate_fault_envelope
from .mission import MissionGenome, MissionPhase, MissionPhaseResult, MissionReport, demo_air_mission, evaluate_mission
from .models import AirfoilPolarConfig, BladeStation, FluidMedium, OperatingPoint, RotorDesign, default_air, default_water, demo_rotor
from .oak import PropulsionOAKReport, run_propulsion_benchmarks
from .optimizer import OptimizationConstraints, OptimizationReport, grid_optimize, scale_rotor
from .polars import PolarEvaluation, PolarRegistry, PolarSample, PolarTable, demo_polar_table
from .r02_oak import R02OAKReport, run_r02_benchmarks
from .r03_oak import R03OAKReport, run_r03_benchmarks
from .robust_mission import MissionUncertaintyCase, RobustMissionCaseResult, RobustMissionReport, default_uncertainty_cases, evaluate_robust_mission
from .structural import BladeMaterial, StructuralAssumptions, StructuralBladeReport, StructuralSectionResult, analyze_blade_structure, default_composite_material

__all__ = [
    "AcousticHarmonic", "AcousticLimits", "AcousticScreenReport", "AirfoilPolarConfig",
    "AnnularBEMAnalysis", "AnnularSectionResult", "BladeMaterial", "BladeStation",
    "CavitationAssessment", "FaultCaseResult", "FaultEnvelopeReport", "FaultPhaseResult",
    "FaultScenario", "FluidMedium", "MissionGenome", "MissionPhase", "MissionPhaseResult",
    "MissionReport", "MissionUncertaintyCase", "OperatingPoint", "OptimizationConstraints",
    "OptimizationReport", "PolarEvaluation", "PolarRegistry", "PolarSample", "PolarTable",
    "PropulsionOAKReport", "R02OAKReport", "R03OAKReport", "RobustMissionCaseResult",
    "RobustMissionReport", "RotorAnalysis", "RotorDesign", "SectionResult",
    "StructuralAssumptions", "StructuralBladeReport", "StructuralSectionResult",
    "analyze_annular_bem", "analyze_blade_structure", "analyze_rotor", "assess_cavitation",
    "cavitation_number", "default_air", "default_composite_material", "default_fault_scenarios",
    "default_uncertainty_cases", "default_water", "demo_air_mission", "demo_polar_table",
    "demo_rotor", "evaluate_fault_envelope", "evaluate_mission", "evaluate_robust_mission",
    "grid_optimize", "run_propulsion_benchmarks", "run_r02_benchmarks", "run_r03_benchmarks",
    "scale_rotor", "screen_rotor_acoustics",
]

__version__ = "0.3.0"
