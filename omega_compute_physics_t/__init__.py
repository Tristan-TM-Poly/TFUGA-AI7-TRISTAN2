"""Ω-COMPUTE-PHYSICS-T∞ / Ω-META-COMPUTE-PHYSICS-T∞.

Empirical, OAK-safe resource modelling and meta-discovery for functions,
pipelines and repository fleets.

Important epistemic rule: fitted finite-domain scaling, static loop-depth hints,
representation compression, residual associations and cross-language static
fingerprints are evidence for planning; they are not mathematical Big-O/Theta
proofs, causal identification, semantic equivalence or sandbox guarantees.
"""

from .active import ExperimentCandidate, discriminating_experiment, geometric_design_space, rank_experiments, select_next_experiments
from .atlas import ComplexityAtlas, EmpiricalResourceModel, ResourceSample
from .benchmark_contract import BenchmarkContract, BenchmarkRisk, InputAxis, gate_contract, load_contract
from .budget import BudgetCompileReport, CandidateEvaluation, ResourceConstraint, compile_budget, pareto_front, quality_per_cost
from .call_graph import CallEdge, CallGraphReport, build_call_graph
from .complexity_diff import ComplexityDiffReport, compare_models, geometric_sweep
from .complexity_ir import FunctionIR, IROp, compile_source_ir
from .contract_planner import ContractPlan, plan_contract
from .dag_resources import DAGEdge, DAGNode, DAGResourceReport, compose_dag
from .fixture_registry import FixtureRegistry, FixtureSpec, conservative_default_registry
from .fleet import FleetAtlas, WorkloadFamily, WorkloadRef, build_fleet_atlas, build_workload_families, global_benchmark_priority
from .fleet_stage_a import FleetStageAReport, StageABenchmarkSeed, StageARepositorySummary, scan_checkout_fleet
from .language_adapters import LanguageAdapterRegistry, LexicalCodeAdapter, PythonAdapter, SourceGenome, default_language_registry
from .machine_genome import MachineGenome, calibrate_machine, fingerprint_machine
from .meta_oak import MetaOAKCheck, MetaOAKReport, audit_representation_candidate, audit_residual_interpretation, audit_theory_ecology, audit_validated_model
from .profiler import ProfileResult, profile_call, profile_pipeline
from .regression_ledger import RegressionEvent, RegressionLedger, event_from_diff
from .representation import DerivedCoordinate, RepresentationScore, best_representation, generate_coordinate_candidates, search_representations, transform_samples
from .repo_scanner import FunctionGenome, ModuleGenome, RepositoryGenome, benchmark_priority, scan_python_source, scan_repository
from .residuals import MissingVariableCandidate, ResidualPoint, ResidualReport, discover_missing_variable_candidates, residual_points
from .risk_preflight import RiskFinding, RiskPreflightReport, scan_source_risk
from .snapshot_ledger import RepositorySnapshot, SnapshotDiff, SnapshotFile, compare_snapshots, snapshot_checkout, snapshot_from_records
from .theory_foundry import FalsificationCandidate, TheoryCandidate, generate_theory_competition, rank_falsification_candidates
from .tropical import DirectionalDominance, ExponentTerm, asymptotic_direction_spectrum, directional_dominance, dominance_signature
from .universal_fleet import UniversalFleetReport, UniversalRepositoryReport, scan_universal_checkout, scan_universal_fleet
from .validation import ConformalInterval, DriftReport, ModelCandidate, ValidatedResourceModel, detect_drift, fit_validated_resource_model

__all__ = [
    "ComplexityAtlas", "EmpiricalResourceModel", "ResourceSample",
    "ProfileResult", "profile_call", "profile_pipeline",
    "ModelCandidate", "ValidatedResourceModel", "ConformalInterval", "DriftReport",
    "fit_validated_resource_model", "detect_drift",
    "ComplexityDiffReport", "compare_models", "geometric_sweep",
    "ExperimentCandidate", "geometric_design_space", "rank_experiments", "select_next_experiments", "discriminating_experiment",
    "ResourceConstraint", "CandidateEvaluation", "BudgetCompileReport", "compile_budget", "pareto_front", "quality_per_cost",
    "DerivedCoordinate", "RepresentationScore", "generate_coordinate_candidates", "transform_samples", "search_representations", "best_representation",
    "ResidualPoint", "MissingVariableCandidate", "ResidualReport", "residual_points", "discover_missing_variable_candidates",
    "TheoryCandidate", "FalsificationCandidate", "generate_theory_competition", "rank_falsification_candidates",
    "MetaOAKCheck", "MetaOAKReport", "audit_validated_model", "audit_representation_candidate", "audit_residual_interpretation", "audit_theory_ecology",
    "FunctionGenome", "ModuleGenome", "RepositoryGenome", "scan_python_source", "scan_repository", "benchmark_priority",
    "WorkloadRef", "WorkloadFamily", "FleetAtlas", "build_workload_families", "build_fleet_atlas", "global_benchmark_priority",
    "BenchmarkContract", "BenchmarkRisk", "InputAxis", "gate_contract", "load_contract",
    "IROp", "FunctionIR", "compile_source_ir",
    "DAGNode", "DAGEdge", "DAGResourceReport", "compose_dag",
    "MachineGenome", "fingerprint_machine", "calibrate_machine",
    "StageARepositorySummary", "StageABenchmarkSeed", "FleetStageAReport", "scan_checkout_fleet",
    "ExponentTerm", "DirectionalDominance", "directional_dominance", "asymptotic_direction_spectrum", "dominance_signature",
    "SnapshotFile", "RepositorySnapshot", "SnapshotDiff", "snapshot_from_records", "snapshot_checkout", "compare_snapshots",
    "CallEdge", "CallGraphReport", "build_call_graph",
    "FixtureSpec", "FixtureRegistry", "conservative_default_registry",
    "RiskFinding", "RiskPreflightReport", "scan_source_risk",
    "ContractPlan", "plan_contract",
    "RegressionEvent", "RegressionLedger", "event_from_diff",
    "SourceGenome", "PythonAdapter", "LexicalCodeAdapter", "LanguageAdapterRegistry", "default_language_registry",
    "UniversalRepositoryReport", "UniversalFleetReport", "scan_universal_checkout", "scan_universal_fleet",
]

__version__ = "0.6.0"
