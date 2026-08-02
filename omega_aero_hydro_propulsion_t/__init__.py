"""Ω-AERO-HYDRO-PROPULSION-T: OAK-safe propulsion research kernels."""

from .acoustics import AcousticHarmonic, AcousticLimits, AcousticScreenReport, screen_rotor_acoustics
from .analysis import RotorAnalysis, SectionResult, analyze_rotor
from .annular_bem import AnnularBEMAnalysis, AnnularSectionResult, analyze_annular_bem
from .cavitation import CavitationAssessment, assess_cavitation, cavitation_number
from .faults import FaultCaseResult, FaultEnvelopeReport, FaultPhaseResult, FaultScenario, default_fault_scenarios, evaluate_fault_envelope
from .materials import MaterialAtlas, MaterialRecord, default_material_atlas
from .mission import MissionGenome, MissionPhase, MissionPhaseResult, MissionReport, demo_air_mission, evaluate_mission
from .models import AirfoilPolarConfig, BladeStation, FluidMedium, OperatingPoint, RotorDesign, default_air, default_water, demo_rotor
from .multifidelity import (
    BackpressureState,
    EvidenceEvent,
    F0ScreenResult,
    FidelityDefinition,
    MergedShardReport,
    MMinusRecord,
    MultiFidelityCampaignReport,
    MultiFidelityCandidate,
    MultiFidelityCheckpoint,
    MultiFidelityPolicy,
    PromotionDecision,
    ResourceEnvelope,
    ShardManifest,
    expanded_fault_scenarios,
    expanded_uncertainty_cases,
    merge_shard_reports,
    plan_shards,
    run_multifidelity_campaign,
    screen_f0,
)
from .oak import PropulsionOAKReport, run_propulsion_benchmarks
from .optimizer import OptimizationConstraints, OptimizationReport, grid_optimize, scale_rotor
from .polars import PolarEvaluation, PolarRegistry, PolarSample, PolarTable, demo_polar_table
from .r02_oak import R02OAKReport, run_r02_benchmarks
from .r03_max_oak import MaxOAKGate, R03MaxOAKReport, run_r03_max_benchmarks
from .r03_oak import R03OAKReport, run_r03_benchmarks
from .r04_oak import R04OAKGate, R04OAKReport, permissive_r04_policy, relaxed_r04_constraints, run_r04_benchmarks
from .robust_mission import MissionUncertaintyCase, RobustMissionCaseResult, RobustMissionReport, default_uncertainty_cases, evaluate_robust_mission
from .structural import BladeMaterial, StructuralAssumptions, StructuralBladeReport, StructuralSectionResult, analyze_blade_structure, default_composite_material
from .system_optimizer import CampaignCheckpoint, InfiniteSystemFrontier, SystemCampaignReport, SystemCandidateResult, SystemDesignVector, SystemObjectives, SystemSearchConstraints, evaluate_system_candidate, run_system_campaign

__all__ = [
    "AcousticHarmonic", "AcousticLimits", "AcousticScreenReport", "AirfoilPolarConfig",
    "AnnularBEMAnalysis", "AnnularSectionResult", "BackpressureState", "BladeMaterial",
    "BladeStation", "CampaignCheckpoint", "CavitationAssessment", "EvidenceEvent",
    "F0ScreenResult", "FaultCaseResult", "FaultEnvelopeReport", "FaultPhaseResult",
    "FaultScenario", "FidelityDefinition", "FluidMedium", "InfiniteSystemFrontier",
    "MaterialAtlas", "MaterialRecord", "MaxOAKGate", "MergedShardReport", "MMinusRecord",
    "MissionGenome", "MissionPhase", "MissionPhaseResult", "MissionReport",
    "MissionUncertaintyCase", "MultiFidelityCampaignReport", "MultiFidelityCandidate",
    "MultiFidelityCheckpoint", "MultiFidelityPolicy", "OperatingPoint",
    "OptimizationConstraints", "OptimizationReport", "PolarEvaluation", "PolarRegistry",
    "PolarSample", "PolarTable", "PromotionDecision", "PropulsionOAKReport",
    "R02OAKReport", "R03MaxOAKReport", "R03OAKReport", "R04OAKGate", "R04OAKReport",
    "ResourceEnvelope", "RobustMissionCaseResult", "RobustMissionReport", "RotorAnalysis",
    "RotorDesign", "SectionResult", "ShardManifest", "StructuralAssumptions",
    "StructuralBladeReport", "StructuralSectionResult", "SystemCampaignReport",
    "SystemCandidateResult", "SystemDesignVector", "SystemObjectives",
    "SystemSearchConstraints", "analyze_annular_bem", "analyze_blade_structure",
    "analyze_rotor", "assess_cavitation", "cavitation_number", "default_air",
    "default_composite_material", "default_fault_scenarios", "default_material_atlas",
    "default_uncertainty_cases", "default_water", "demo_air_mission", "demo_polar_table",
    "demo_rotor", "evaluate_fault_envelope", "evaluate_mission",
    "evaluate_robust_mission", "evaluate_system_candidate", "expanded_fault_scenarios",
    "expanded_uncertainty_cases", "grid_optimize", "merge_shard_reports",
    "permissive_r04_policy", "plan_shards", "relaxed_r04_constraints",
    "run_multifidelity_campaign", "run_propulsion_benchmarks", "run_r02_benchmarks",
    "run_r03_benchmarks", "run_r03_max_benchmarks", "run_r04_benchmarks",
    "run_system_campaign", "scale_rotor", "screen_f0", "screen_rotor_acoustics",
]

__version__ = "0.4.0"
