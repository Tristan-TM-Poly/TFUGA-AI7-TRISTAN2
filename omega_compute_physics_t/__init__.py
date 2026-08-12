"""Ω-COMPUTE-PHYSICS-T∞ / Ω-META-COMPUTE-PHYSICS-T∞.

Empirical, OAK-safe resource modelling and meta-discovery for functions,
pipelines and repository fleets.

Important epistemic rule: fitted finite-domain scaling, static loop-depth hints,
representation compression and residual associations are empirical evidence, not
mathematical Big-O/Theta proofs or causal identification.
"""

from .active import (
    ExperimentCandidate,
    discriminating_experiment,
    geometric_design_space,
    rank_experiments,
    select_next_experiments,
)
from .atlas import ComplexityAtlas, EmpiricalResourceModel, ResourceSample
from .budget import (
    BudgetCompileReport,
    CandidateEvaluation,
    ResourceConstraint,
    compile_budget,
    pareto_front,
    quality_per_cost,
)
from .complexity_diff import ComplexityDiffReport, compare_models, geometric_sweep
from .fleet import (
    FleetAtlas,
    WorkloadFamily,
    WorkloadRef,
    build_fleet_atlas,
    build_workload_families,
    global_benchmark_priority,
)
from .meta_oak import (
    MetaOAKCheck,
    MetaOAKReport,
    audit_representation_candidate,
    audit_residual_interpretation,
    audit_theory_ecology,
    audit_validated_model,
)
from .profiler import ProfileResult, profile_call, profile_pipeline
from .representation import (
    DerivedCoordinate,
    RepresentationScore,
    best_representation,
    generate_coordinate_candidates,
    search_representations,
    transform_samples,
)
from .repo_scanner import (
    FunctionGenome,
    ModuleGenome,
    RepositoryGenome,
    benchmark_priority,
    scan_python_source,
    scan_repository,
)
from .residuals import (
    MissingVariableCandidate,
    ResidualPoint,
    ResidualReport,
    discover_missing_variable_candidates,
    residual_points,
)
from .theory_foundry import (
    FalsificationCandidate,
    TheoryCandidate,
    generate_theory_competition,
    rank_falsification_candidates,
)
from .validation import (
    ConformalInterval,
    DriftReport,
    ModelCandidate,
    ValidatedResourceModel,
    detect_drift,
    fit_validated_resource_model,
)

__all__ = [
    "ComplexityAtlas",
    "EmpiricalResourceModel",
    "ResourceSample",
    "ProfileResult",
    "profile_call",
    "profile_pipeline",
    "ModelCandidate",
    "ValidatedResourceModel",
    "ConformalInterval",
    "DriftReport",
    "fit_validated_resource_model",
    "detect_drift",
    "ComplexityDiffReport",
    "compare_models",
    "geometric_sweep",
    "ExperimentCandidate",
    "geometric_design_space",
    "rank_experiments",
    "select_next_experiments",
    "discriminating_experiment",
    "ResourceConstraint",
    "CandidateEvaluation",
    "BudgetCompileReport",
    "compile_budget",
    "pareto_front",
    "quality_per_cost",
    "DerivedCoordinate",
    "RepresentationScore",
    "generate_coordinate_candidates",
    "transform_samples",
    "search_representations",
    "best_representation",
    "ResidualPoint",
    "MissingVariableCandidate",
    "ResidualReport",
    "residual_points",
    "discover_missing_variable_candidates",
    "TheoryCandidate",
    "FalsificationCandidate",
    "generate_theory_competition",
    "rank_falsification_candidates",
    "MetaOAKCheck",
    "MetaOAKReport",
    "audit_validated_model",
    "audit_representation_candidate",
    "audit_residual_interpretation",
    "audit_theory_ecology",
    "FunctionGenome",
    "ModuleGenome",
    "RepositoryGenome",
    "scan_python_source",
    "scan_repository",
    "benchmark_priority",
    "WorkloadRef",
    "WorkloadFamily",
    "FleetAtlas",
    "build_workload_families",
    "build_fleet_atlas",
    "global_benchmark_priority",
]

__version__ = "0.4.0"
