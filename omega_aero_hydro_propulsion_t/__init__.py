"""Ω-AERO-HYDRO-PROPULSION-T: OAK-safe propulsion research kernels."""

from .acoustics import AcousticHarmonic, AcousticLimits, AcousticScreenReport, screen_rotor_acoustics
from .analysis import RotorAnalysis, SectionResult, analyze_rotor
from .annular_bem import AnnularBEMAnalysis, AnnularSectionResult, analyze_annular_bem
from .architecture_compiler import (
    ArchitectureCandidate,
    ArchitectureCompilationReport,
    ArchitectureTemplate,
    PropulsionMissionIntent,
    compile_propulsion_architectures,
    default_architecture_templates,
    infer_domain,
)
from .cavitation import CavitationAssessment, assess_cavitation, cavitation_number
from .evidence_discrepancy import (
    DiscrepancyRecord,
    DiscrepancyTensorReport,
    MetricObservation,
    build_discrepancy_tensor,
    demo_discrepancy_tensor,
)
from .evidence_ladder import (
    EvidenceLadderReport,
    EvidenceReceipt,
    ReceiptAssessment,
    assess_evidence_ladder,
    assess_receipt,
    computational_receipts,
)
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
from .r05_oak import R05OAKGate, R05OAKReport, demo_air_intent, demo_water_intent, run_r05_benchmarks
from .robust_mission import MissionUncertaintyCase, RobustMissionCaseResult, RobustMissionReport, default_uncertainty_cases, evaluate_robust_mission
from .structural import BladeMaterial, StructuralAssumptions, StructuralBladeReport, StructuralSectionResult, analyze_blade_structure, default_composite_material
from .system_optimizer import CampaignCheckpoint, InfiniteSystemFrontier, SystemCampaignReport, SystemCandidateResult, SystemDesignVector, SystemObjectives, SystemSearchConstraints, evaluate_system_candidate, run_system_campaign
from .wake_graph import (
    Vector3,
    VortexSegment,
    WakeConfig,
    WakeGraphReport,
    WakeNode,
    WakeProbe,
    analyze_wake_graph,
    induced_velocity,
    induced_velocity_from_segment,
)

__all__ = [
    "AcousticHarmonic", "AcousticLimits", "AcousticScreenReport", "AirfoilPolarConfig",
    "AnnularBEMAnalysis", "AnnularSectionResult", "ArchitectureCandidate",
    "ArchitectureCompilationReport", "ArchitectureTemplate", "BackpressureState",
    "BladeMaterial", "BladeStation", "CampaignCheckpoint", "CavitationAssessment",
    "DiscrepancyRecord", "DiscrepancyTensorReport", "EvidenceEvent", "EvidenceLadderReport",
    "EvidenceReceipt", "F0ScreenResult", "FaultCaseResult", "FaultEnvelopeReport",
    "FaultPhaseResult", "FaultScenario", "FidelityDefinition", "FluidMedium",
    "InfiniteSystemFrontier", "MaterialAtlas", "MaterialRecord", "MaxOAKGate",
    "MergedShardReport", "MetricObservation", "MMinusRecord", "MissionGenome",
    "MissionPhase", "MissionPhaseResult", "MissionReport", "MissionUncertaintyCase",
    "MultiFidelityCampaignReport", "MultiFidelityCandidate", "MultiFidelityCheckpoint",
    "MultiFidelityPolicy", "OperatingPoint", "OptimizationConstraints", "OptimizationReport",
    "PolarEvaluation", "PolarRegistry", "PolarSample", "PolarTable", "PromotionDecision",
    "PropulsionMissionIntent", "PropulsionOAKReport", "R02OAKReport", "R03MaxOAKReport",
    "R03OAKReport", "R04OAKGate", "R04OAKReport", "R05OAKGate", "R05OAKReport",
    "ReceiptAssessment", "ResourceEnvelope", "RobustMissionCaseResult", "RobustMissionReport",
    "RotorAnalysis", "RotorDesign", "SectionResult", "ShardManifest", "StructuralAssumptions",
    "StructuralBladeReport", "StructuralSectionResult", "SystemCampaignReport",
    "SystemCandidateResult", "SystemDesignVector", "SystemObjectives", "SystemSearchConstraints",
    "Vector3", "VortexSegment", "WakeConfig", "WakeGraphReport", "WakeNode", "WakeProbe",
    "analyze_annular_bem", "analyze_blade_structure", "analyze_rotor", "analyze_wake_graph",
    "assess_cavitation", "assess_evidence_ladder", "assess_receipt",
    "build_discrepancy_tensor", "cavitation_number", "compile_propulsion_architectures",
    "computational_receipts", "default_air", "default_architecture_templates",
    "default_composite_material", "default_fault_scenarios", "default_material_atlas",
    "default_uncertainty_cases", "default_water", "demo_air_intent", "demo_air_mission",
    "demo_discrepancy_tensor", "demo_polar_table", "demo_rotor", "demo_water_intent",
    "evaluate_fault_envelope", "evaluate_mission", "evaluate_robust_mission",
    "evaluate_system_candidate", "expanded_fault_scenarios", "expanded_uncertainty_cases",
    "grid_optimize", "induced_velocity", "induced_velocity_from_segment", "infer_domain",
    "merge_shard_reports", "permissive_r04_policy", "plan_shards", "relaxed_r04_constraints",
    "run_multifidelity_campaign", "run_propulsion_benchmarks", "run_r02_benchmarks",
    "run_r03_benchmarks", "run_r03_max_benchmarks", "run_r04_benchmarks",
    "run_r05_benchmarks", "run_system_campaign", "scale_rotor", "screen_f0",
    "screen_rotor_acoustics",
]

__version__ = "0.5.0"
